"""Load the Elsayed et al. (Sci. Data 2026) 8-GPU H100/B200 training power traces.

Source: figshare DOI 10.6084/m9.figshare.31654879 (single zip). The figshare page says CC BY 4.0
but the README inside the zip says CC BY-NC-ND 4.0; treat it as non-commercial until resolved.

Only the 8-GPU node sessions (Node_Dataset/*.csv) are used; the RTX 3060 single-machine sessions
(HWiNFO, Windows) are skipped. Logger is pynvml at 20 ms rows, but nvmlDeviceGetPowerUsage on
H100/B200 is a 1 s trailing average that refreshes about every 100 ms, so the 0.2 s grid below
does not hide any real sub-second detail.

Output tables (written to data/processed/):
  ext_elsayed_traces.parquet  long format: trace_id, t_s, power_w (node total, 8 GPUs), gpu0_w..gpu7_w
  ext_elsayed_meta.csv        one row per unique session (duplicate files across folders removed)
"""
from __future__ import annotations

import hashlib
import re
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np
import pandas as pd

from src.config import DT_S, PROC_DIR, RAW_DIR, SEED
from src.load import _finish, resample_uniform

URL = "https://ndownloader.figshare.com/files/62953543"
ZIP_MD5 = "f44c1bccc233ffe11916432d720a8034"
EL_DIR: Path = RAW_DIR / "elsayed"
EL_ZIP: Path = EL_DIR / "elsayed.zip"
EXTRACT_DIR: Path = EL_DIR / "extracted"
DONE_FLAG: Path = EXTRACT_DIR / ".extracted_ok"

GPU_MAX_W = 1200.0  # above any plausible H100/B200 reading; treated as a sensor glitch
N_GPUS = 8
# Per-GPU rated power. H100 SXM = 700 W (the logged gpu*_Power_TDP percent implies 700 W).
# B200: 1000 W used here; the paper/README gives no TDP for B200, the logged percent is checked in build().
GPU_RATED_W: dict[str, float] = {"H100": 700.0, "B200": 1000.0}
WORKLOADS: dict[str, str] = {
    "Text Generation LLMs": "elsayed_llm_finetune",
    "Image Generation Diffusion Models": "elsayed_diffusion",
}
NAME_RE = re.compile(r"_(H100|B200)_8GPU_Node_")
PARAMS: dict[str, re.Pattern] = {
    "seq_len": re.compile(r"SeqLength(\d+)"),
    "zero_stage": re.compile(r"_z(\d)_"),
    "batch_size": re.compile(r"BatchSize(\d+)"),
    "base_channels": re.compile(r"ModelSize(\d+)"),  # diffusion UNet base channels (128/256/512)
    "image_size": re.compile(r"ImageSize(\d+)"),
}


def download_and_extract() -> None:
    """Fetch the zip and extract only the 8-GPU node CSVs. Safe to call repeatedly."""
    if DONE_FLAG.exists():
        return
    EL_DIR.mkdir(parents=True, exist_ok=True)
    if not EL_ZIP.exists():
        tmp = EL_ZIP.with_suffix(".part")
        urllib.request.urlretrieve(URL, tmp)
        tmp.rename(EL_ZIP)
    md5 = hashlib.md5(EL_ZIP.read_bytes()).hexdigest()
    if md5 != ZIP_MD5:
        raise ValueError(f"MD5 mismatch for {EL_ZIP}: {md5}")
    n = 0
    with zipfile.ZipFile(EL_ZIP) as zf:
        for info in zf.infolist():
            parts = PurePosixPath(info.filename).parts
            if "Node_Dataset" not in parts or not info.filename.lower().endswith(".csv"):
                continue
            if not NAME_RE.search(parts[-1]) or ".." in parts or info.filename.startswith("/"):
                continue
            rel = Path(*parts[parts.index("Node_Dataset") + 1:])  # untrusted names: no traversal
            dest = EXTRACT_DIR / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as out:
                out.write(src.read())
            n += 1
    if n == 0:
        raise ValueError("No 8-GPU node CSVs found in the zip")
    DONE_FLAG.write_text(f"{n} files\n")
    EL_ZIP.unlink()  # disk is tight; the flag keeps this idempotent


def _parse_name(path: Path) -> dict:
    stem = path.stem
    hw = NAME_RE.search(stem).group(1)
    workload = WORKLOADS[path.relative_to(EXTRACT_DIR).parts[0]]
    if workload == "elsayed_llm_finetune":
        model = re.search(r"Lamma(\d+B)", stem).group(1).lower()  # authors spell it "Lamma"
        model = f"llama{model}"
    else:
        model = f"diffusion_c{PARAMS['base_channels'].search(stem).group(1)}"
    row = {"hw": hw, "workload": workload, "model": model}
    for k, rx in PARAMS.items():
        m = rx.search(stem)
        row[k] = int(m.group(1)) if m else np.nan
    return row


def read_session(path: Path) -> pd.DataFrame:
    """Per-GPU power in watts indexed by timestamp."""
    cols = ["timestamp"] + [f"gpu{i}_power_W" for i in range(N_GPUS)]
    df = pd.read_csv(path, usecols=cols)
    out = pd.DataFrame(index=pd.to_datetime(df["timestamp"], format="ISO8601"))
    for i in range(N_GPUS):
        w = pd.to_numeric(df[f"gpu{i}_power_W"], errors="coerce").to_numpy(dtype=float, copy=True)
        w[(w > GPU_MAX_W) | (w < 0)] = np.nan  # sensor glitches
        out[f"gpu{i}_w"] = w
    return out[~out.index.duplicated()].sort_index()


def assign_splits(meta: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Whole sessions to one split, stratified by (hw, workload): roughly 60/20/20."""
    rng = np.random.default_rng(seed)
    meta = meta.copy()
    meta["split"] = ""
    for _, g in meta.groupby(["hw", "workload"]):
        ids = np.array(sorted(g["job_id"]))
        rng.shuffle(ids)
        n = len(ids)
        n_test = max(1, round(0.2 * n))
        n_val = max(1, round(0.2 * n)) if n >= 3 else 0
        lab = {j: "test" for j in ids[:n_test]}
        lab.update({j: "val" for j in ids[n_test:n_test + n_val]})
        lab.update({j: "train" for j in ids[n_test + n_val:]})
        meta.loc[g.index, "split"] = g["job_id"].map(lab)
    return meta


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (traces, meta) for every unique 8-GPU session."""
    download_and_extract()
    seen: dict[str, int] = {}
    frames: list[pd.DataFrame] = []
    rows: list[dict] = []
    for p in sorted(EXTRACT_DIR.rglob("*.csv")):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        folder = p.parent.name
        if digest in seen:  # the same session is copied into several "impact" folders
            rows[seen[digest]]["folders"] += f";{folder}"
            continue
        info = _parse_name(p)
        tid = f"elsayed_{p.stem.lower()}"
        if any(r["trace_id"] == tid for r in rows):  # same name, different content
            tid = f"{tid}_{digest[:8]}"
        fr = _finish(resample_uniform(read_session(p)), tid)
        frames.append(fr.drop(columns="timestamp"))
        seen[digest] = len(rows)
        rows.append({
            "trace_id": tid, "dataset": "elsayed", "workload": info["workload"],
            "model": info["model"], "hw": info["hw"], "n_gpus": N_GPUS,
            "rated_w": N_GPUS * GPU_RATED_W[info["hw"]], "phase": "training", "node_count": 1,
            "job_id": tid, "node": f"{info['hw'].lower()}_node",
            "duration_s": float(fr["t_s"].iloc[-1]),
            **{k: info[k] for k in PARAMS}, "folders": folder,
        })
    meta = assign_splits(pd.DataFrame(rows))
    traces = pd.concat(frames, ignore_index=True)
    traces["trace_id"] = traces["trace_id"].astype("category")
    return traces, meta


def drop_summary(traces: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Mean power as fraction of rated and big-drop counts, with power scaled to a 4xH100 (2800 W) node."""
    from src.events import detect_drops

    out = []
    for tid, g in traces.groupby("trace_id", observed=True):
        m = meta.set_index("trace_id").loc[tid]
        p = g["power_w"].to_numpy(dtype=float)
        out.append({"hw": m["hw"], "workload": m["workload"], "mean_frac_rated": p.mean() / m["rated_w"],
                    "n_drops": len(detect_drops(p * 2800.0 / m["rated_w"])), "hours": len(p) * DT_S / 3600})
    d = pd.DataFrame(out).groupby(["hw", "workload"])
    return d.agg(sessions=("n_drops", "size"), mean_frac_rated=("mean_frac_rated", "mean"),
                 drops=("n_drops", "sum"), hours=("hours", "sum"))


def build() -> None:
    """Parse the raw CSVs, write the processed tables and print a summary."""
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    traces, meta = load()
    traces.to_parquet(PROC_DIR / "ext_elsayed_traces.parquet", index=False)
    meta.to_csv(PROC_DIR / "ext_elsayed_meta.csv", index=False)
    meta["hours"] = meta["duration_s"] / 3600
    print(meta.groupby(["hw", "workload", "split"]).agg(sessions=("trace_id", "size"),
                                                        hours=("hours", "sum")).round(2))
    print(len(traces), "samples,", len(meta), "unique sessions")
    print(drop_summary(traces, meta).round(3))


if __name__ == "__main__":
    build()
