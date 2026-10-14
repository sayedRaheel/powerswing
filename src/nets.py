"""Step 5 (PyTorch part): a tiny causal TCN and zero-shot Amazon Chronos-Bolt-Small.

Run as its own process (`python -m src.nets`) because PyTorch and LightGBM ship different OpenMP
runtimes that crash when loaded in one process on macOS. Reads the feature tables written by
src.modeling, writes predictions to data/processed/nets_*.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
import torch
from torch import nn

from src.config import HORIZONS_S, PROC_DIR, SEED
from src.features import H_STEPS
from src.load import load_traces
from src.utils import power_dict, time_per_call

# ----------------------------------------------------------------------------- TCN

TCN_WINDOW = 256  # 51.2 s of history at 5 Hz
P_SCALE = 1000.0  # watts per unit inside the network


class CausalBlock(nn.Module):
    def __init__(self, ch: int, dilation: int, k: int = 3, dropout: float = 0.05) -> None:
        super().__init__()
        self.pad = (k - 1) * dilation
        self.c1 = nn.Conv1d(ch, ch, k, dilation=dilation)
        self.c2 = nn.Conv1d(ch, ch, k, dilation=dilation)
        self.act = nn.GELU()
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.act(self.c1(nn.functional.pad(x, (self.pad, 0))))
        y = self.drop(y)
        y = self.act(self.c2(nn.functional.pad(y, (self.pad, 0))))
        return x + y


class TinyTCN(nn.Module):
    """Dilated causal conv stack. Receptive field 1 + 2*2*(1+2+...+64) = 509 >= window."""

    def __init__(self, ch: int = 32, dilations: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64)) -> None:
        super().__init__()
        self.inp = nn.Conv1d(3, ch, 1)
        self.blocks = nn.Sequential(*[CausalBlock(ch, d) for d in dilations])
        self.head = nn.Sequential(nn.Linear(ch + 3, 64), nn.GELU(), nn.Linear(64, len(HORIZONS_S) + 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, 3, window)
        z = self.blocks(self.inp(x))[:, :, -1]
        return self.head(torch.cat([z, x[:, :, -1]], dim=1))


def n_params(m: nn.Module) -> int:
    return sum(p.numel() for p in m.parameters())


def make_windows(p: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Input tensor (len(idx), 3, TCN_WINDOW) for decision times idx.

    Channels: absolute level, level relative to the current sample, 1-step difference.
    """
    pad = np.concatenate([np.full(TCN_WINDOW, p[0]), p])
    rel = idx[:, None] + TCN_WINDOW + np.arange(-TCN_WINDOW + 1, 1)[None, :]
    w = pad[rel]
    cur = w[:, -1:]
    d = np.diff(w, axis=1, prepend=w[:, :1])
    return np.stack([w / P_SCALE - 2.0, (w - cur) / P_SCALE, d / P_SCALE * 5], axis=1).astype(np.float32)


class Packed:
    """All traces concatenated once (each left-padded by TCN_WINDOW) so a batch is one gather."""

    def __init__(self, arrs: dict[str, np.ndarray]) -> None:
        parts, self.offset = [], {}
        pos = 0
        for tid, p in arrs.items():
            seg = np.concatenate([np.full(TCN_WINDOW, p[0]), p])
            self.offset[tid] = pos + TCN_WINDOW
            parts.append(seg)
            pos += len(seg)
        self.big = np.concatenate(parts).astype(np.float32)
        self.rel = np.arange(-TCN_WINDOW + 1, 1)

    def rows_index(self, rows: pd.DataFrame) -> np.ndarray:
        """Absolute position of each row's decision sample inside `big`."""
        off = rows["trace_id"].map(self.offset).to_numpy()
        return (off + rows["idx"].to_numpy()).astype(np.int64)

    def windows(self, g: np.ndarray) -> np.ndarray:
        w = self.big[g[:, None] + self.rel[None, :]]
        cur = w[:, -1:]
        d = np.diff(w, axis=1, prepend=w[:, :1])
        return np.stack([w / P_SCALE - 2.0, (w - cur) / P_SCALE, d / P_SCALE * 5], axis=1)

    def targets(self, g: np.ndarray, ydrop: np.ndarray) -> np.ndarray:
        cols = [(self.big[g + H_STEPS[h]] - self.big[g]) / P_SCALE for h in HORIZONS_S]
        return np.stack(cols + [ydrop.astype(np.float32)], axis=1).astype(np.float32)


def _batches(pk: Packed, rows: pd.DataFrame, bs: int, shuffle: bool, rng: np.random.Generator):
    g_all = pk.rows_index(rows)
    ydrop = rows["y_drop"].to_numpy()
    order = rng.permutation(len(rows)) if shuffle else np.arange(len(rows))
    for s in range(0, len(order), bs):
        o = order[s : s + bs]
        g = g_all[o]
        yield torch.from_numpy(pk.windows(g)), torch.from_numpy(pk.targets(g, ydrop[o])), o


def _device() -> torch.device:
    return torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")


def train_tcn(arrs: dict[str, np.ndarray], train_rows: pd.DataFrame, val_rows: pd.DataFrame,
              epochs: int = 6, bs: int = 512, lr: float = 2e-3, log=print) -> TinyTCN:
    """Multi-task training: L1 on the three horizon deltas + weighted BCE on the drop label.

    Trains on Apple-GPU (MPS) when available; inference latency is still measured on CPU.
    """
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    dev = _device()
    pk = Packed(arrs)
    model = TinyTCN().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    steps = epochs * int(np.ceil(len(train_rows) / bs))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps)
    pos = train_rows["y_drop"].mean()
    bce = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(np.sqrt((1 - pos) / max(pos, 1e-6))), device=dev))
    best, best_state = np.inf, None
    for ep in range(epochs):
        model.train()
        t0, tot, nb = time.time(), 0.0, 0
        for xb, yb, _ in _batches(pk, train_rows, bs, True, rng):
            xb, yb = xb.to(dev), yb.to(dev)
            out = model(xb)
            loss = nn.functional.l1_loss(out[:, :-1], yb[:, :-1]) + 0.5 * bce(out[:, -1], yb[:, -1])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item()
            nb += 1
        vloss = _eval_loss(model, pk, val_rows, bce, dev)
        log(f"  TCN epoch {ep + 1}/{epochs} train {tot / nb:.4f} val {vloss:.4f} ({time.time() - t0:.0f}s, {dev})")
        if vloss < best:
            best, best_state = vloss, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    model = TinyTCN()
    model.load_state_dict(best_state)
    model.eval()
    return model


@torch.no_grad()
def _eval_loss(model: TinyTCN, pk: Packed, rows: pd.DataFrame, bce, dev) -> float:
    model.eval()
    tot, n = 0.0, 0
    for xb, yb, _ in _batches(pk, rows, 4096, False, np.random.default_rng(0)):
        xb, yb = xb.to(dev), yb.to(dev)
        out = model(xb)
        loss = nn.functional.l1_loss(out[:, :-1], yb[:, :-1]) + 0.5 * bce(out[:, -1], yb[:, -1])
        tot += loss.item() * len(xb)
        n += len(xb)
    return tot / n


@torch.no_grad()
def predict_tcn(model: TinyTCN, arrs: dict[str, np.ndarray], rows: pd.DataFrame) -> tuple[dict[int, np.ndarray], np.ndarray]:
    """Forecasts (watts) per horizon and drop probability, aligned with `rows`."""
    dev = _device()
    model = model.to(dev).eval()
    pk = Packed(arrs)
    out = np.zeros((len(rows), len(HORIZONS_S) + 1), dtype=np.float32)
    for xb, _, o in _batches(pk, rows, 8192, False, np.random.default_rng(0)):
        out[o] = model(xb.to(dev)).cpu().numpy()
    model.to("cpu")
    p = rows["p"].to_numpy()
    fc = {h: p + out[:, i] * P_SCALE for i, h in enumerate(HORIZONS_S)}
    return fc, 1 / (1 + np.exp(-out[:, -1]))


# ----------------------------------------------------------------------------- Chronos

CHRONOS_CONTEXT = 512  # 102 s of history


def load_chronos(name: str = "amazon/chronos-bolt-small"):
    from chronos import BaseChronosPipeline

    return BaseChronosPipeline.from_pretrained(name, device_map="cpu", torch_dtype=torch.float32)


@torch.no_grad()
def predict_chronos(pipe, arrs: dict[str, np.ndarray], rows: pd.DataFrame, bs: int = 64) -> dict[int, np.ndarray]:
    """Zero-shot median forecast at each horizon for every row."""
    max_h = max(H_STEPS.values())
    tids = rows["trace_id"].to_numpy()
    idx = rows["idx"].to_numpy().astype(int)
    out = {h: np.zeros(len(rows)) for h in HORIZONS_S}
    for s in range(0, len(rows), bs):
        ctx = []
        for tid, i in zip(tids[s : s + bs], idx[s : s + bs]):
            p = arrs[tid]
            ctx.append(torch.tensor(p[max(0, i - CHRONOS_CONTEXT + 1) : i + 1], dtype=torch.float32))
        q, _ = pipe.predict_quantiles(ctx, prediction_length=max_h, quantile_levels=[0.5])
        med = q[:, :, 0].numpy()
        for h in HORIZONS_S:
            out[h][s : s + bs] = med[:, H_STEPS[h] - 1]
    return out




def load_timesfm(context: int = CHRONOS_CONTEXT, horizon: int = 64):
    import timesfm

    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
    model.compile(timesfm.ForecastConfig(
        max_context=context, max_horizon=horizon, normalize_inputs=True,
        use_continuous_quantile_head=True, force_flip_invariance=True,
        infer_is_positive=True, fix_quantile_crossing=True,
    ))
    return model


def predict_timesfm(model, arrs: dict[str, np.ndarray], rows: pd.DataFrame, bs: int = 64) -> dict[int, np.ndarray]:
    """Zero-shot point forecast from Google TimesFM 2.5 (200M) at each horizon."""
    max_h = max(H_STEPS.values())
    tids = rows["trace_id"].to_numpy()
    idx = rows["idx"].to_numpy().astype(int)
    out = {h: np.zeros(len(rows)) for h in HORIZONS_S}
    for s in range(0, len(rows), bs):
        ctx = [arrs[t][max(0, i - CHRONOS_CONTEXT + 1) : i + 1].astype(np.float32)
               for t, i in zip(tids[s : s + bs], idx[s : s + bs])]
        point, _ = model.forecast(horizon=max_h, inputs=ctx)
        for h in HORIZONS_S:
            out[h][s : s + bs] = point[:, H_STEPS[h] - 1]
    return out


# ----------------------------------------------------------------------------- process entry point

CHRONOS_PER_WORKLOAD = 400  # test points per workload for the (slow) zero-shot model


def chronos_subset(te: pd.DataFrame) -> np.ndarray:
    """Stratified random test rows (same rows are used to score every model against Chronos)."""
    rng = np.random.default_rng(SEED)
    return np.concatenate([
        rng.choice(np.flatnonzero((te["workload"] == w).to_numpy()), CHRONOS_PER_WORKLOAD, replace=False)
        for w in sorted(te["workload"].unique())
    ])


def run(log=print) -> None:
    """Train the TCN, predict val/test, run Chronos on the subset, time both. Writes nets_* files."""
    torch.manual_seed(SEED)
    torch.set_num_threads(8)
    cols = ["trace_id", "idx", "y_drop", "workload", "p"]
    tr = pd.read_parquet(PROC_DIR / "table_train.parquet", columns=cols)
    va = pd.read_parquet(PROC_DIR / "table_val.parquet", columns=cols)
    te = pd.read_parquet(PROC_DIR / "table_test.parquet", columns=cols)
    traces, _ = load_traces(only_model=True)
    power = power_dict(traces)

    t0 = time.time()
    tcn = train_tcn(power, tr, va.iloc[::10], log=log)
    fc, score_te = predict_tcn(tcn, power, te)
    fc_va, score_va = predict_tcn(tcn, power, va)
    pd.DataFrame({f"tcn_{h}s": fc_va[h].astype(np.float32) for h in HORIZONS_S}).to_parquet(
        PROC_DIR / "nets_val_forecast_tcn.parquet", index=False)  # used for validation-only model selection
    torch.save(tcn.state_dict(), PROC_DIR / "tcn.pt")
    out = pd.DataFrame({f"tcn_{h}s": fc[h].astype(np.float32) for h in HORIZONS_S})
    out["score_tcn"] = score_te.astype(np.float32)
    out.to_parquet(PROC_DIR / "nets_test.parquet", index=False)
    np.save(PROC_DIR / "nets_val_score_tcn.npy", score_va.astype(np.float32))
    log(f"TCN ({n_params(tcn):,} params) trained and predicted in {time.time() - t0:.0f}s")

    sub_idx = chronos_subset(te)
    np.save(PROC_DIR / "chronos_subset_idx.npy", sub_idx)
    hist = power[te["trace_id"].iloc[0]][:1200]
    torch.set_num_threads(1)
    x = torch.from_numpy(make_windows(hist, np.array([len(hist) - 1])))
    with torch.no_grad():
        lat = {f"tiny TCN ({n_params(tcn):,} params, all 4 outputs)": time_per_call(lambda: tcn(x), 300)}
    torch.set_num_threads(8)
    t0 = time.time()
    try:
        pipe = load_chronos()
        ch = predict_chronos(pipe, power, te.iloc[sub_idx].reset_index(drop=True))
        pd.DataFrame({f"chronos_bolt_small_{h}s": ch[h] for h in HORIZONS_S}).to_parquet(PROC_DIR / "nets_chronos.parquet", index=False)
        log(f"Chronos-Bolt-Small zero-shot on {len(sub_idx)} points in {time.time() - t0:.0f}s")
        torch.set_num_threads(1)
        ctx = [torch.tensor(hist[-CHRONOS_CONTEXT:], dtype=torch.float32)]
        n_ch = sum(p.numel() for p in pipe.model.parameters())
        lat[f"chronos-bolt-small ({n_ch / 1e6:.0f}M params, zero-shot)"] = time_per_call(
            lambda: pipe.predict_quantiles(ctx, prediction_length=max(H_STEPS.values()), quantile_levels=[0.5]), 30)
    except Exception as e:  # pretrained weights unavailable offline etc.
        log(f"Chronos skipped: {e!r}")
        (PROC_DIR / "nets_chronos.parquet").unlink(missing_ok=True)
    torch.set_num_threads(8)
    t0 = time.time()
    try:
        tfm = load_timesfm()
        tf = predict_timesfm(tfm, power, te.iloc[sub_idx].reset_index(drop=True))
        pd.DataFrame({f"timesfm_2p5_{h}s": tf[h] for h in HORIZONS_S}).to_parquet(PROC_DIR / "nets_timesfm.parquet", index=False)
        log(f"TimesFM 2.5 zero-shot on {len(sub_idx)} points in {time.time() - t0:.0f}s")
        torch.set_num_threads(1)
        ctx1 = [hist[-CHRONOS_CONTEXT:].astype(np.float32)]
        lat["timesfm-2.5 (200M params, zero-shot)"] = time_per_call(
            lambda: tfm.forecast(horizon=max(H_STEPS.values()), inputs=ctx1), 20)
    except Exception as e:
        log(f"TimesFM skipped: {e!r}")
        (PROC_DIR / "nets_timesfm.parquet").unlink(missing_ok=True)
    json.dump(lat, open(PROC_DIR / "nets_latency.json", "w"), indent=1)


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run(log=lambda m: print(m, flush=True))
