"""Streaming loader for a labelled subset of the MIT Supercloud Dataset (V100 GPU power traces).

LICENSE NOTE: the MIT Supercloud Dataset is licensed CC BY-NC-ND 4.0
(http://creativecommons.org/licenses/by-nc-nd/4.0/). It is used here for academic research only.
Never redistribute the raw CSVs or the reduced tables written by this module, never use them
commercially, and cite Samsi et al., "The MIT Supercloud Dataset", IEEE HPEC 2021.

Source: public bucket s3://mit-supercloud-dataset/datacenter-challenge/202201/ (read anonymously
over HTTPS). GPU files are gpu/<NNNN>/<id_job>-<node>.csv, where <node> is the anonymised hostname
"r<rack>-n<id>" exactly as in the slurm-log.csv `nodelist` column, so one file holds one (job, node).
Each node has 2 V100 GPUs (power limit 250 W), sampled by nvidia-smi roughly every 100 ms.
GPU timestamps sit a whole number of hours (4 h in summer) before the Slurm job window: they are
local wall time stored as epoch seconds. The window check estimates and removes that shift.

Disk budget: files are streamed one at a time into data/raw/supercloud/tmp/, reduced, and deleted
immediately; at most RAW_CAP_BYTES of raw CSV exist on disk at any moment. The reduction is
resumable: a file whose stats JSON already exists in data/raw/supercloud/reduced/ is skipped.

Output tables (written to data/processed/):
  ext_supercloud_traces.parquet    trace_id, t_s, power_w (node total), timestamp
  ext_supercloud_meta.csv          one row per trace: trace_id, dataset, workload, model, hw, n_gpus,
                                   rated_w, phase, node_count, job_id, node, duration_s, split
  ext_supercloud_class_counts.csv  labelled jobs available vs selected per model class

Run end to end with `python -m src.ext_supercloud` (progress in data/raw/supercloud/progress.log).
"""
from __future__ import annotations

import json
import logging
import math
import re
import shutil
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DT_S, PROC_DIR, RAW_DIR, SEED
from src.load import resample_uniform

BASE_URL = "https://mit-supercloud-dataset.s3.amazonaws.com"
PREFIX = "datacenter-challenge/202201/"

SC_DIR: Path = RAW_DIR / "supercloud"
TMP_DIR: Path = SC_DIR / "tmp"
RED_DIR: Path = SC_DIR / "reduced"
LOG_PATH: Path = SC_DIR / "progress.log"
LISTING_PATH: Path = SC_DIR / "gpu_listing.csv"
SELECTION_PATH: Path = SC_DIR / "selection.csv"
TRACES_PATH: Path = PROC_DIR / "ext_supercloud_traces.parquet"
META_PATH: Path = PROC_DIR / "ext_supercloud_meta.csv"
COUNTS_PATH: Path = PROC_DIR / "ext_supercloud_class_counts.csv"

SLURM_MAX_BYTES = 300e6  # slurm-log.csv is about 100 MB; skip it if it ever grows past this
RAW_CAP_BYTES = 2e9  # most raw CSV allowed on disk at once
RAW_BUDGET_BYTES = 60e9  # total raw download budget for the selection
N_THREADS = 8

JOBS_PER_CLASS = 80  # 7 classes -> about 560 jobs
MIN_JOBS_PER_CLASS = 30
MULTI_NODE_SHARE = 1 / 3  # at least this share of each class is multi-node where available
MAX_NODES_PER_JOB = 4
PREF_DUR_S = (600.0, 3 * 3600.0)  # preferred job duration
FALLBACK_MIN_DUR_S = 300.0

GPU_MIN_W, GPU_MAX_W = 0.0, 400.0  # V100 readings outside this range are sensor errors
RATED_PER_GPU_W = 250.0
MIN_SEGMENT_S = 300.0
TS_SLACK_S = 600.0  # samples further than this outside the Slurm job window count as bad timestamps

FILE_RE = re.compile(r"/(\d+)-(r\d+-n\d+)\.csv$")

log = logging.getLogger("ext_supercloud")


def setup_logging() -> None:
    SC_DIR.mkdir(parents=True, exist_ok=True)
    if log.handlers:
        return
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for h in (logging.FileHandler(LOG_PATH), logging.StreamHandler()):
        h.setFormatter(fmt)
        log.addHandler(h)


def model_class(model: str) -> str:
    """Map a fine-grained label (e.g. 'resnet50_v1.5', 'U3-64', 'schnet') to its model class."""
    m = model.lower()
    for prefix in ("vgg", "resnet", "inception", "distilbert", "bert"):
        if m.startswith(prefix):
            return prefix
    if re.match(r"u\d", m):
        return "unet"
    return "gnn"  # dimenet, schnet, pna, conv (NNConv)


# ---------------------------------------------------------------------------- download helpers

def _get(url: str, dest: Path | None = None, retries: int = 4) -> bytes | None:
    """GET a URL, streaming to `dest` if given. Retries with backoff."""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                if dest is None:
                    return r.read()
                with open(dest, "wb") as f:
                    shutil.copyfileobj(r, f, length=1 << 20)
                return None
        except Exception as e:  # noqa: BLE001  (network errors come in many types)
            if attempt == retries - 1:
                raise
            log.warning("retry %d for %s: %s", attempt + 1, url, e)
            time.sleep(2 ** attempt)
    return None


def _head_size(key: str) -> int:
    req = urllib.request.Request(f"{BASE_URL}/{PREFIX}{key}", method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def fetch_small(name: str) -> Path:
    """Download a top-level bucket file once into SC_DIR."""
    out = SC_DIR / name
    if not out.exists():
        part = out.with_suffix(".part")
        _get(f"{BASE_URL}/{PREFIX}{name}", part)
        part.rename(out)
    return out


def fetch_labels() -> pd.DataFrame:
    """labelled_jobids.csv with an added model class column."""
    lab = pd.read_csv(fetch_small("labelled_jobids.csv"), dtype={"id_job": str})
    lab["model_class"] = lab["model"].map(model_class)
    return lab


def fetch_slurm() -> pd.DataFrame | None:
    """Job start/end and node count from slurm-log.csv, or None if the file is too large."""
    size = _head_size("slurm-log.csv")
    if size > SLURM_MAX_BYTES:
        log.info("slurm-log.csv is %.0f MB, skipping; durations come from the data", size / 1e6)
        return None
    s = pd.read_csv(fetch_small("slurm-log.csv"), dtype={"id_job": str},
                    usecols=["id_job", "nodes_alloc", "time_start", "time_end", "state"])
    s["dur_s"] = (s["time_end"] - s["time_start"]).astype(float)
    return s


def list_gpu_files() -> pd.DataFrame:
    """Key listing of gpu/ (job_id, node, key, size), cached as CSV."""
    if LISTING_PATH.exists():
        return pd.read_csv(LISTING_PATH, dtype={"job_id": str})
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    rows: list[tuple[str, str, str, int]] = []
    token: str | None = None
    while True:
        q = {"list-type": "2", "prefix": PREFIX + "gpu/", "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        root = ET.fromstring(_get(f"{BASE_URL}/?{urllib.parse.urlencode(q)}"))
        for c in root.findall("s3:Contents", ns):
            key = c.findtext("s3:Key", namespaces=ns)
            m = FILE_RE.search(key)
            if m:
                rows.append((m.group(1), m.group(2), key[len(PREFIX):],
                             int(c.findtext("s3:Size", namespaces=ns))))
        if root.findtext("s3:IsTruncated", namespaces=ns) != "true":
            break
        token = root.findtext("s3:NextContinuationToken", namespaces=ns)
    df = pd.DataFrame(rows, columns=["job_id", "node", "key", "size"])
    df.to_csv(LISTING_PATH, index=False)
    log.info("listed %d GPU files (%.1f GB)", len(df), df["size"].sum() / 1e9)
    return df


# ---------------------------------------------------------------------------- selection

def select_jobs(seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pick labelled jobs per model class. Returns (files to fetch, class counts).

    Per class: JOBS_PER_CLASS jobs, preferring PREF_DUR_S durations, with at least
    MULTI_NODE_SHARE multi-node jobs where available. All nodes of a selected job are kept,
    capped at MAX_NODES_PER_JOB (first nodes by name). Subsampled further if over the raw budget.
    """
    rng = np.random.default_rng(seed)
    lab = fetch_labels()
    files = list_gpu_files()
    files = files[files["job_id"].isin(set(lab["id_job"]))]
    jobs = lab.rename(columns={"id_job": "job_id"})
    jobs = jobs[jobs["job_id"].isin(set(files["job_id"]))].copy()
    slurm = fetch_slurm()
    if slurm is not None:
        jobs = jobs.merge(slurm.rename(columns={"id_job": "job_id"}), on="job_id", how="left")
    else:
        # Without Slurm times the duration is approximated from file size (about 830 B/s per node).
        per_node = files.groupby("job_id")["size"].mean()
        jobs["dur_s"] = jobs["job_id"].map(per_node) / 830.0
        jobs["time_start"], jobs["time_end"] = np.nan, np.nan
    files = files.sort_values(["job_id", "node"])
    node_count = files.groupby("job_id").size()
    kept = files.groupby("job_id").head(MAX_NODES_PER_JOB)
    jobs["node_count"] = jobs["job_id"].map(node_count)
    jobs["raw_bytes"] = jobs["job_id"].map(kept.groupby("job_id")["size"].sum())
    jobs["pref"] = jobs["dur_s"].between(*PREF_DUR_S)
    jobs = jobs.sort_values("job_id").reset_index(drop=True)

    chosen: list[str] = []
    for cls, g in jobs.groupby("model_class", sort=True):
        target = min(len(g), JOBS_PER_CLASS)
        pref = g[g["pref"]]
        multi = pref[pref["node_count"] > 1]["job_id"].to_numpy()
        n_multi = min(len(multi), math.ceil(target * MULTI_NODE_SHARE))
        pick = list(rng.choice(multi, n_multi, replace=False)) if n_multi else []
        rest = pref[~pref["job_id"].isin(pick)]["job_id"].to_numpy()
        n_rest = min(len(rest), target - len(pick))
        pick += list(rng.choice(rest, n_rest, replace=False)) if n_rest else []
        if len(pick) < target:  # not enough preferred jobs: fall back to any job >= 5 min
            fb = g[~g["job_id"].isin(pick) & (g["dur_s"] >= FALLBACK_MIN_DUR_S)]["job_id"].to_numpy()
            n_fb = min(len(fb), target - len(pick))
            pick += list(rng.choice(fb, n_fb, replace=False)) if n_fb else []
        if len(pick) < MIN_JOBS_PER_CLASS:
            log.warning("class %s: only %d jobs selected", cls, len(pick))
        chosen += pick

    sel = jobs[jobs["job_id"].isin(chosen)].copy()
    while sel["raw_bytes"].sum() > RAW_BUDGET_BYTES:  # subsample whole jobs to fit the budget
        drop = rng.choice(sel["job_id"].to_numpy(), max(1, len(sel) // 20), replace=False)
        sel = sel[~sel["job_id"].isin(drop)]

    counts = pd.DataFrame({
        "jobs_available": jobs.groupby("model_class").size(),
        "jobs_pref_duration": jobs[jobs["pref"]].groupby("model_class").size(),
        "jobs_multinode_available": jobs[jobs["node_count"] > 1].groupby("model_class").size(),
        "jobs_selected": sel.groupby("model_class").size(),
        "jobs_multinode_selected": sel[sel["node_count"] > 1].groupby("model_class").size(),
        "raw_gb_selected": sel.groupby("model_class")["raw_bytes"].sum() / 1e9,
    }).fillna(0).rename_axis("model_class").reset_index()

    out = kept.merge(sel[["job_id", "model", "model_class", "node_count", "dur_s",
                          "time_start", "time_end"]], on="job_id")
    out.to_csv(SELECTION_PATH, index=False)
    return out, counts


# ---------------------------------------------------------------------------- per-file reduction

def reduce_csv(path: Path, trace_base: str, t_window: tuple[float, float] | None = None
               ) -> tuple[pd.DataFrame | None, dict]:
    """Reduce one job-node CSV to node power on the uniform grid, split at gaps > 2 s.

    Returns (segments in long format or None, stats dict).
    """
    df = pd.read_csv(path, usecols=["timestamp", "gpu_index", "power_draw_W"])
    st: dict = {"n_rows": int(len(df))}
    ts = pd.to_numeric(df["timestamp"], errors="coerce")
    pw = pd.to_numeric(df["power_draw_W"], errors="coerce")
    gi = pd.to_numeric(df["gpu_index"], errors="coerce")
    bad_ts = ts.isna() | gi.isna()
    st["tz_offset_h"] = np.nan
    if t_window is not None and not any(np.isnan(t_window)) and ts.notna().any():
        # GPU epochs are local wall time read as UTC: a whole-hour shift (-4 h in EDT) vs Slurm.
        off = round((ts.median() - (t_window[0] + t_window[1]) / 2) / 3600.0) * 3600.0
        st["tz_offset_h"] = off / 3600.0
        bad_ts |= (ts < t_window[0] + off - TS_SLACK_S) | (ts > t_window[1] + off + TS_SLACK_S)
    bad_pw = pw.isna() | (pw < GPU_MIN_W) | (pw > GPU_MAX_W)
    st["n_bad_ts"] = int(bad_ts.sum())
    st["n_bad_power"] = int((bad_pw & ~bad_ts).sum())
    st["n_backwards_ts"] = int(sum((np.diff(ts[gi == g].to_numpy()) < 0).sum()
                                   for g in gi.dropna().unique()))
    ok = ~bad_ts & ~bad_pw
    d = pd.DataFrame({"ts": ts[ok], "gpu": gi[ok].astype(int), "w": pw[ok]})
    st["n_gpus"] = int(d["gpu"].nunique())
    if d.empty:
        st.update(median_dt_s=np.nan, span_s=0.0, n_segments_raw=0, n_segments=0, kept_s=0.0)
        return None, st
    d = d.sort_values(["gpu", "ts"]).drop_duplicates(["gpu", "ts"])
    st["median_dt_s"] = float(np.nanmedian(np.concatenate(
        [np.diff(g["ts"].to_numpy()) for _, g in d.groupby("gpu")] + [np.array([np.nan])])))
    st["span_s"] = float(d["ts"].max() - d["ts"].min())

    wide = d.pivot_table(index="ts", columns="gpu", values="w", aggfunc="mean").sort_index()
    wide.columns = [f"gpu{int(c)}_w" for c in wide.columns]
    wide.index = pd.to_datetime(wide.index, unit="s")
    # Default origin floors to the 0.2 s epoch grid, so nodes of one job share a grid.
    r = resample_uniform(wide)
    valid = r.notna().all(axis=1).to_numpy()
    # Runs of valid rows; any invalid row means a gap > 2 s (or a silent GPU), so split there.
    edges = np.diff(np.concatenate([[0], valid.astype(int), [0]]))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    st["n_segments_raw"] = int(len(starts))
    min_rows = int(MIN_SEGMENT_S / DT_S)
    segs: list[pd.DataFrame] = []
    for k, (a, b) in enumerate(zip(starts, ends)):
        if b - a < min_rows:
            continue
        chunk = r.iloc[a:b]
        tid = trace_base if len(starts) == 1 else f"{trace_base}_s{k}"
        segs.append(pd.DataFrame({
            "trace_id": tid,
            "t_s": (chunk.index - chunk.index[0]).total_seconds(),
            "power_w": chunk.sum(axis=1).to_numpy(dtype=np.float32),
            "timestamp": chunk.index,
        }))
    st["n_segments"] = len(segs)
    st["kept_s"] = float(sum(len(s) for s in segs) * DT_S)
    return (pd.concat(segs, ignore_index=True) if segs else None), st


class DiskBudget:
    """Blocks a download until its bytes fit under the raw-CSV cap."""

    def __init__(self, cap: float) -> None:
        self.cap, self.used = cap, 0.0
        self.cv = threading.Condition()

    def acquire(self, n: float) -> None:
        with self.cv:
            self.cv.wait_for(lambda: self.used == 0 or self.used + n <= self.cap)
            self.used += n

    def release(self, n: float) -> None:
        with self.cv:
            self.used -= n
            self.cv.notify_all()


def _stem(job_id: str, node: str) -> str:
    return f"{job_id}-{node}"


def process_one(row: pd.Series, budget: DiskBudget) -> dict:
    """Download, reduce and delete one CSV. Idempotent: skips files already reduced."""
    stem = _stem(row["job_id"], row["node"])
    stats_path = RED_DIR / f"{stem}.json"
    if stats_path.exists():
        return json.loads(stats_path.read_text())
    tmp = TMP_DIR / f"{stem}.csv"
    budget.acquire(row["size"])
    try:
        _get(f"{BASE_URL}/{PREFIX}{row['key']}", tmp)
        seg, st = reduce_csv(tmp, f"sc_{stem}", (row["time_start"], row["time_end"]))
    finally:
        tmp.unlink(missing_ok=True)  # raw CSV never outlives its reduction
        budget.release(row["size"])
    if seg is not None:
        seg.to_parquet(RED_DIR / f"{stem}.parquet", index=False)
    st.update(job_id=row["job_id"], node=row["node"], raw_bytes=int(row["size"]))
    stats_path.write_text(json.dumps(st))  # written last: marks the file as done
    return st


def stream_reduce(sel: pd.DataFrame, n_threads: int = N_THREADS) -> pd.DataFrame:
    """Reduce every selected file in parallel under the disk cap. Returns per-file stats."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    RED_DIR.mkdir(parents=True, exist_ok=True)
    for p in TMP_DIR.glob("*.csv"):  # leftovers from an interrupted run
        p.unlink()
    budget = DiskBudget(RAW_CAP_BYTES)
    total, done, t0 = len(sel), 0, time.time()
    stats: list[dict] = []
    with ThreadPoolExecutor(n_threads) as ex:
        futs = {ex.submit(process_one, r, budget): r for _, r in sel.iterrows()}
        for f in as_completed(futs):
            r = futs[f]
            try:
                stats.append(f.result())
            except Exception as e:  # noqa: BLE001  (one bad file should not stop the run)
                log.error("failed %s: %s", r["key"], e)
            done += 1
            if done % 25 == 0 or done == total:
                log.info("%d/%d files (%.0f s elapsed)", done, total, time.time() - t0)
    return pd.DataFrame(stats)


# ---------------------------------------------------------------------------- assembly

def assign_splits(meta: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Whole jobs to train/val/test about 60/20/20, stratified by model class."""
    rng = np.random.default_rng(seed)
    meta = meta.copy()
    meta["split"] = ""
    for _, g in meta.groupby("workload", sort=True):
        jobs = np.array(sorted(g["job_id"].unique()))
        rng.shuffle(jobs)
        n = len(jobs)
        n_test = max(1, round(0.2 * n))
        n_val = max(1, round(0.2 * n)) if n >= 3 else 0
        lab = {j: "test" for j in jobs[:n_test]}
        lab.update({j: "val" for j in jobs[n_test:n_test + n_val]})
        lab.update({j: "train" for j in jobs[n_test + n_val:]})
        meta.loc[g.index, "split"] = g["job_id"].map(lab)
    return meta


def assemble(sel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Concatenate reduced files into the processed traces and meta tables."""
    frames: list[pd.DataFrame] = []
    rows: list[dict] = []
    info = sel.set_index(["job_id", "node"])
    for (job, node), r in info.iterrows():
        stem = _stem(job, node)
        p, sp = RED_DIR / f"{stem}.parquet", RED_DIR / f"{stem}.json"
        if not p.exists() or not sp.exists():
            continue
        st = json.loads(sp.read_text())
        seg = pd.read_parquet(p)
        frames.append(seg)
        for tid, g in seg.groupby("trace_id", sort=True):
            rows.append({
                "trace_id": tid, "dataset": "supercloud", "workload": f"sc_{r['model_class']}",
                "model": r["model"], "hw": "V100", "n_gpus": st["n_gpus"],
                "rated_w": RATED_PER_GPU_W * st["n_gpus"], "phase": "training",
                "node_count": int(r["node_count"]), "job_id": job, "node": node,
                "duration_s": float(g["t_s"].iloc[-1]),
            })
    traces = pd.concat(frames, ignore_index=True)
    traces["trace_id"] = traces["trace_id"].astype("category")
    meta = assign_splits(pd.DataFrame(rows))
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    traces.to_parquet(TRACES_PATH, index=False)
    meta.to_csv(META_PATH, index=False)
    return traces, meta


# ---------------------------------------------------------------------------- summary

def summarize(traces: pd.DataFrame, meta: pd.DataFrame, stats: pd.DataFrame,
              counts: pd.DataFrame) -> None:
    """Print the dataset summary used to sanity-check the subset."""
    from src.events import detect_drops

    print("\nClass counts (available vs selected):")
    print(counts.to_string(index=False))
    m = meta.copy()
    m["hours"] = m["duration_s"] / 3600
    print("\nJobs per class/split:")
    print(m.groupby(["workload", "split"])["job_id"].nunique().unstack(fill_value=0))
    print("\nNode-hours per class/split:")
    print(m.groupby(["workload", "split"])["hours"].sum().unstack(fill_value=0).round(1))

    traces = traces.copy()
    traces["trace_id"] = traces["trace_id"].astype(str)
    per: list[dict] = []
    rated = m.set_index("trace_id")["rated_w"]
    for tid, g in traces.groupby("trace_id", sort=True):
        p = g["power_w"].to_numpy(dtype=float)
        rw = rated[tid]
        frac = p / rw
        per.append({"trace_id": tid, "mean_frac": frac.mean(), "std_w": p.std(),
                    "idle_frac": (frac < 0.3).mean(),
                    "n_drops": len(detect_drops(p * 2800.0 / rw)), "hours": len(p) * DT_S / 3600})
    pt = pd.DataFrame(per).merge(m[["trace_id", "workload", "n_gpus", "job_id"]], on="trace_id")
    agg = pt.groupby("workload").apply(lambda g: pd.Series({
        "mean_power_frac_rated": np.average(g["mean_frac"], weights=g["hours"]),
        "drops": g["n_drops"].sum(), "node_hours": g["hours"].sum(),
        "drops_per_node_hour": g["n_drops"].sum() / g["hours"].sum(),
    }), include_groups=False)
    print("\nPower and big drops (detect_drops on power_w * 2800 / rated_w):")
    print(agg.round(3))
    print(f"All: mean power/rated {np.average(pt['mean_frac'], weights=pt['hours']):.3f}, "
          f"{pt['n_drops'].sum()} drops / {pt['hours'].sum():.1f} node-h = "
          f"{pt['n_drops'].sum() / pt['hours'].sum():.2f} per node-hour")
    print(f"GPUs per node file: {m['n_gpus'].value_counts().to_dict()}")

    print(f"\nMedian sampling interval before resampling: {stats['median_dt_s'].median():.3f} s "
          f"(p10 {stats['median_dt_s'].quantile(0.1):.3f}, p90 {stats['median_dt_s'].quantile(0.9):.3f})")
    mj = m.groupby("job_id")["node_count"].first()
    print(f"Multi-node jobs: {(mj > 1).sum()} of {len(mj)} "
          f"(node_count distribution {mj.value_counts().sort_index().to_dict()})")
    print(f"Raw downloaded: {stats['raw_bytes'].sum() / 1e9:.2f} GB in {len(stats)} files")
    for p in (TRACES_PATH, META_PATH, COUNTS_PATH):
        print(f"{p.name}: {p.stat().st_size / 1e6:.1f} MB")

    print("\nOddities:")
    print(f"  files with no segment >= 5 min: {(stats['n_segments'] == 0).sum()}")
    print(f"  files split at gaps > 2 s: {(stats['n_segments_raw'] > 1).sum()}")
    print(f"  bad timestamps (NaN or outside Slurm window +-10 min): {stats['n_bad_ts'].sum()} rows "
          f"in {(stats['n_bad_ts'] > 0).sum()} files")
    print(f"  GPU-vs-Slurm clock offset (h): {stats['tz_offset_h'].value_counts().to_dict()}")
    print(f"  backwards timestamps: {stats['n_backwards_ts'].sum()} in "
          f"{(stats['n_backwards_ts'] > 0).sum()} files")
    print(f"  bad power readings dropped: {stats['n_bad_power'].sum()} rows")
    print(f"  idle-dominated traces (>50% of samples below 30% rated): {(pt['idle_frac'] > 0.5).sum()} "
          f"of {len(pt)}")
    print(f"  flat traces (power std < 5 W): {(pt['std_w'] < 5).sum()}")
    print(f"  traces with zero big drops: {(pt['n_drops'] == 0).sum()}")


def main() -> None:
    setup_logging()
    log.info("selecting jobs")
    sel, counts = select_jobs()
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    counts.to_csv(COUNTS_PATH, index=False)
    log.info("selected %d jobs, %d files, %.2f GB raw", sel["job_id"].nunique(), len(sel),
             sel["size"].sum() / 1e9)
    stats = stream_reduce(sel)
    log.info("assembling processed tables")
    traces, meta = assemble(sel)
    log.info("wrote %d traces, %d samples", meta.shape[0], len(traces))
    summarize(traces, meta, stats, counts)


if __name__ == "__main__":
    main()
