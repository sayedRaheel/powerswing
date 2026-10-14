"""Load the NLR GenAI power-profile dataset into clean, uniformly sampled per-node traces.

Output tables (written to data/processed/):
  traces.parquet       long format, one row per (trace_id, sample):
                       trace_id, t_s, power_w (node total, 4 GPUs), gpu0_w..gpu3_w
  traces_meta.csv      one row per trace: workload, model, phase, node_count, job_id, node,
                       duration_s, split, use_for_model
  jobs.parquet         job-level GPU power (sum over all nodes of a training job)

Only GPU (NVML) power is used. CPU (RAPL) logs exist in the dataset but are out of scope.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    DT_S,
    INFERENCE_BLOCK_S,
    MAX_NODES_PER_JOB_MODEL,
    NLR_DIR,
    PROC_DIR,
    SEED,
    ZIP_PATH,
)

DATETIME_FORMAT = "%Y-%m-%d_%H:%M:%S.%f"
GPU_MAX_W = 800.0  # the dataset authors treat per-GPU readings above this as sensor errors
MAX_INTERP_S = 2.0  # gaps up to this long are forward-filled, longer ones stay NaN

TRAINING_DIRS: dict[str, str] = {
    "training_llama2_70b_lora": "llama2_70b_lora",
    "training_stable_diffusion": "stable_diffusion",
}
INFERENCE_DIRS: dict[str, str] = {
    "inference_offline_llama3_70b": "inference_offline",
    "inference_online_finite_llama3_70b": "inference_online_finite",
    "inference_online_rate_llama3_70b": "inference_online_rate",
}
FNAME_RE = re.compile(r"nvml_wattameter_emissions_parsed_slurmid_(\d+)_node_(\w+)\.log")


@dataclass
class TraceMeta:
    trace_id: str
    workload: str  # e.g. "train_llama2_70b_lora", "inference_offline"
    phase: str  # "training" | "inference"
    model: str
    node_count: int
    job_id: str
    node: str
    duration_s: float = 0.0


def ensure_unzipped() -> None:
    """Unzip the raw archive if it has not been extracted yet."""
    if (NLR_DIR / "00_raw_datasets").exists():
        return
    if not ZIP_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found. Place the NLR ZIP at {ZIP_PATH} "
            "(https://data.nlr.gov/system/files/312/1775845072-dataset.zip)."
        )
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zf.extractall(NLR_DIR)


def read_nvml_log(path: Path) -> pd.DataFrame:
    """Parse one WattAMeter NVML log. Returns per-GPU power in watts indexed by timestamp."""
    header: list[str] | None = None
    with open(path) as f:
        for line in f:
            if line.startswith("#") and "timestamp" in line:
                header = line.lstrip("# ").split()
                break
    if header is None:
        raise ValueError(f"No header in {path}")
    df = pd.read_csv(path, sep=r"\s+", comment="#", header=None)
    df = df.iloc[:, : len(header)]
    df.columns = header
    df["timestamp"] = pd.to_datetime(df["timestamp"], format=DATETIME_FORMAT)
    gpu_cols = [c for c in header if c.startswith("gpu-") and c.endswith("[mW]")]
    out = pd.DataFrame(index=df["timestamp"])
    for i, c in enumerate(sorted(gpu_cols)):
        w = df[c].to_numpy(dtype=float) / 1e3
        w[(w > GPU_MAX_W) | (w < 0)] = np.nan  # sensor glitches
        out[f"gpu{i}_w"] = w
    out = out[~out.index.duplicated()].sort_index()
    return out


def resample_uniform(df: pd.DataFrame, origin: pd.Timestamp | None = None) -> pd.DataFrame:
    """Average onto a uniform DT_S grid, forward-fill short gaps, keep long gaps as NaN."""
    rule = f"{int(DT_S * 1000)}ms"
    origin = origin if origin is not None else df.index[0].floor(rule)
    r = df.resample(rule, origin=origin).mean()
    limit = int(MAX_INTERP_S / DT_S)
    r = r.ffill(limit=limit)  # causal: a missing bin repeats the last reading (never uses the next one)
    return r


def _finish(r: pd.DataFrame, trace_id: str) -> pd.DataFrame:
    gpu_cols = [c for c in r.columns if c.startswith("gpu")]
    r = r.dropna(subset=gpu_cols, how="any")
    out = r[gpu_cols].copy()
    out.insert(0, "power_w", r[gpu_cols].sum(axis=1))
    out.insert(0, "t_s", (r.index - r.index[0]).total_seconds())
    out.insert(0, "trace_id", trace_id)
    out["timestamp"] = r.index
    return out.reset_index(drop=True)


def load_training() -> tuple[list[pd.DataFrame], list[TraceMeta], pd.DataFrame]:
    """One trace per (job, node). Also returns job-level summed GPU power."""
    frames: list[pd.DataFrame] = []
    metas: list[TraceMeta] = []
    jobs: list[pd.DataFrame] = []
    base = NLR_DIR / "00_raw_datasets"
    for dname, model in TRAINING_DIRS.items():
        for node_dir in sorted((base / dname).iterdir()):
            n_nodes = int(node_dir.name.replace("node", ""))
            by_job: dict[str, list[tuple[str, pd.DataFrame]]] = {}
            for p in sorted(node_dir.glob("nvml_*.log")):
                m = FNAME_RE.match(p.name)
                if not m:
                    continue
                job, node = m.group(1), m.group(2)
                by_job.setdefault(job, []).append((node, read_nvml_log(p)))
            for job, nodes in by_job.items():
                origin = min(d.index[0] for _, d in nodes).floor(f"{int(DT_S * 1000)}ms")
                job_series = []
                for node, d in nodes:
                    tid = f"train_{model}_{n_nodes}n_{job}_{node}"
                    r = resample_uniform(d, origin=origin)
                    fr = _finish(r, tid)
                    frames.append(fr)
                    metas.append(
                        TraceMeta(tid, f"train_{model}", "training", model, n_nodes, job, node,
                                  float(fr["t_s"].iloc[-1]))
                    )
                    job_series.append(r.sum(axis=1, min_count=1).rename(node))
                # Job total: sum across nodes only where every node reported.
                jdf = pd.concat(job_series, axis=1)
                jtot = jdf.dropna(how="any").sum(axis=1)
                jobs.append(pd.DataFrame({
                    "job_id": job, "workload": f"train_{model}", "node_count": n_nodes,
                    "t_s": (jtot.index - jtot.index[0]).total_seconds(), "power_w": jtot.to_numpy(),
                }))
    return frames, metas, pd.concat(jobs, ignore_index=True)


def load_inference() -> tuple[list[pd.DataFrame], list[TraceMeta]]:
    """Each inference workload is one long single-node session; cut into fixed time blocks."""
    frames: list[pd.DataFrame] = []
    metas: list[TraceMeta] = []
    base = NLR_DIR / "00_raw_datasets"
    for dname, workload in INFERENCE_DIRS.items():
        logs = sorted((base / dname).glob("nvml_*.log"))
        assert len(logs) == 1, logs
        node = logs[0].stem.split("-")[-1].replace("nvml_wattameter_", "")
        r = resample_uniform(read_nvml_log(logs[0]))
        n_block = int(INFERENCE_BLOCK_S / DT_S)
        for b, start in enumerate(range(0, len(r), n_block)):
            chunk = r.iloc[start:start + n_block]
            if len(chunk) < n_block // 2:  # drop a short tail block
                continue
            tid = f"{workload}_b{b:02d}"
            fr = _finish(chunk, tid)
            frames.append(fr)
            metas.append(TraceMeta(tid, workload, "inference", "llama3_70b", 1, workload, node,
                                   float(fr["t_s"].iloc[-1])))
    return frames, metas


def assign_splits(meta: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Leakage-free splits.

    Training: whole jobs go to one split, stratified by (model, node_count): roughly 60/20/20.
    Inference: time-ordered blocks, first 60% train, next 20% val, last 20% test.
    Also flags `use_for_model`: at most MAX_NODES_PER_JOB_MODEL nodes per training job
    (nodes in one job are near-identical, so extra nodes add cost but little information).
    """
    rng = np.random.default_rng(seed)
    meta = meta.copy()
    meta["split"] = ""
    tr = meta["phase"] == "training"
    for _, g in meta[tr].groupby(["model", "node_count"]):
        jobs = np.array(sorted(g["job_id"].unique()))
        rng.shuffle(jobs)
        n = len(jobs)
        n_test = max(1, round(0.2 * n))
        n_val = max(1, round(0.2 * n)) if n >= 3 else 0
        lab = {j: "test" for j in jobs[:n_test]}
        lab.update({j: "val" for j in jobs[n_test:n_test + n_val]})
        lab.update({j: "train" for j in jobs[n_test + n_val:]})
        meta.loc[g.index, "split"] = g["job_id"].map(lab)
    for _, g in meta[~tr].groupby("workload"):
        g = g.sort_values("trace_id")
        n = len(g)
        cut1, cut2 = int(round(0.6 * n)), int(round(0.8 * n))
        lab = ["train"] * cut1 + ["val"] * (cut2 - cut1) + ["test"] * (n - cut2)
        meta.loc[g.index, "split"] = lab
    meta["use_for_model"] = True
    for _, g in meta[tr].groupby("job_id"):
        keep = sorted(g["node"])[:MAX_NODES_PER_JOB_MODEL]
        meta.loc[g.index, "use_for_model"] = g["node"].isin(keep)
    return meta


def build_processed() -> None:
    """Parse all raw logs and write the processed tables."""
    ensure_unzipped()
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    tf, tm, jobs = load_training()
    inf_f, inf_m = load_inference()
    traces = pd.concat(tf + inf_f, ignore_index=True)
    meta = pd.DataFrame([m.__dict__ for m in tm + inf_m])
    meta = assign_splits(meta)
    traces["trace_id"] = traces["trace_id"].astype("category")
    traces.to_parquet(PROC_DIR / "traces.parquet", index=False)
    meta.to_csv(PROC_DIR / "traces_meta.csv", index=False)
    jobs.to_parquet(PROC_DIR / "jobs.parquet", index=False)


def load_traces(only_model: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (traces, meta). Builds the processed cache on first call."""
    if not (PROC_DIR / "traces.parquet").exists():
        build_processed()
    meta = pd.read_csv(PROC_DIR / "traces_meta.csv", dtype={"job_id": str})
    traces = pd.read_parquet(PROC_DIR / "traces.parquet")
    traces["trace_id"] = traces["trace_id"].astype(str)
    if only_model:
        meta = meta[meta["use_for_model"]]
        traces = traces[traces["trace_id"].isin(set(meta["trace_id"]))]
    return traces, meta


def iter_traces(traces: pd.DataFrame, ids: list[str] | None = None):
    """Yield (trace_id, power array) in a stable order."""
    for tid, g in traces.groupby("trace_id", sort=True, observed=True):
        if ids is not None and tid not in ids:
            continue
        yield tid, g["power_w"].to_numpy(dtype=float)


if __name__ == "__main__":
    build_processed()
    t, m = load_traces()
    print(m.groupby(["workload", "node_count", "split"]).size())
    print(len(t), "samples")
