#!/usr/bin/env python3
"""
Corpus Feasibility Audit (Real-time, Strict Evidence Mode)
=========================================================

Runs a full corpus audit over all in-use job profiles (from core_workforce_current)
and evaluates feasibility for every non-self pair using:

- Strict evidence rules (no predictions without observed data, no movement defaults)
- Sanity checks (volume/recency/mobility/career progression)
- Ensemble model predictions (only after gates pass)
- Weighted feasibility score (same as runtime predictor)

No CLI arguments: paths and thresholds are set below. Outputs an aggregated
diagnostics report to console with a progress bar.
"""

from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter, defaultdict
import time
try:
    import psutil  # optional
except Exception:
    psutil = None
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from tqdm import tqdm


# ---------------------------
# Configuration (edit here)
# ---------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "models" / "2025-Q3" / "business_context.sqlite"
DEFAULT_MODELS_DIR = PROJECT_ROOT / "models" / "2025-Q3"

# Strict evidence thresholds
RWA_MIN = 1.0  # minimum recency-weighted activity
MIN_TOTAL_MOVEMENTS = 3  # minimum total movements for the pair
MIN_TRANSITION_MONTHS = 3  # minimum number of monthly observations
MIN_SOURCE_MOBILITY = 10.0  # floor for source mobility
MIN_TARGET_MOBILITY = 10.0  # floor for target mobility

# Career logic thresholds
MAX_LEVEL_JUMP_WITHOUT_STRONG_EVIDENCE = 1  # allow +/-1 level by default
STRONG_EVIDENCE_MOVES = 10  # if >1 level jump, require at least this many movements
STRONG_EVIDENCE_MONTHS = 6  # and at least this many months observed

# Diagnostics: also run predictions for all pairs (even if not feasible) to view spread
RUN_PREDICTIONS_FOR_ALL_PAIRS = True


# ---------------------------
# Utility dataclasses
# ---------------------------
@dataclass
class GlobalContext:
    jobs_metadata: Dict[str, Dict[str, Any]]
    function_hierarchy: Dict[str, int]
    source_mobility: Dict[str, float]
    target_mobility: Dict[str, float]
    recency_decay: float


# ---------------------------
# Metadata / Models
# ---------------------------
def load_model_metadata(models_dir: Path) -> Tuple[List[str], float, Dict[str, str]]:
    candidates = [
        models_dir / "model_metadata.json",
        models_dir / "ml-training-metadata.json",
        Path("ml-training-metadata.json"),
    ]
    metadata_path = next((p for p in candidates if p.exists()), None)
    if not metadata_path:
        raise FileNotFoundError(f"Model metadata not found in: {candidates}")
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    feature_columns = meta.get("feature_columns", [])
    recency_decay = (
        meta.get("ml_config", {}).get("recency_decay_rate", 0.4)
        if isinstance(meta.get("ml_config"), dict)
        else 0.4
    )
    # Standard filenames
    model_files = {
        "Random Forest": "random_forest_model.joblib",
        "Gradient Boosting": "gradient_boosting_model.joblib",
        "XGBoost": "xgboost_model.joblib",
    }
    return feature_columns, float(recency_decay), model_files


def load_models(models_dir: Path, model_files: Dict[str, str]) -> Dict[str, Any]:
    models: Dict[str, Any] = {}
    for name, fname in model_files.items():
        path = models_dir / fname
        if path.exists():
            models[name] = joblib.load(path)
    if not models:
        raise RuntimeError("No models could be loaded from models directory")
    return models


# ---------------------------
# Global Context Loaders
# ---------------------------
def load_jobs_metadata(conn: sqlite3.Connection) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int]]:
    q = """
        SELECT JobProfileID, JobProfile, JobFunction, JobSubFunction,
               ManagementLevel, JobCategory
        FROM core_job_architecture
        ORDER BY JobProfile
    """
    df = pd.read_sql_query(q, conn)
    jobs: Dict[str, Dict[str, Any]] = {}
    for _, row in df.iterrows():
        jid = str(row["JobProfileID"])
        jobs[jid] = {
            "JobProfile": row["JobProfile"],
            "JobFunction": row["JobFunction"],
            "JobSubFunction": row["JobSubFunction"],
            "ManagementLevel": row["ManagementLevel"],
            "JobCategory": row["JobCategory"],
        }
    funcs = sorted(df["JobFunction"].dropna().unique())
    fh = {func: idx for idx, func in enumerate(funcs)}
    return jobs, fh


def calculate_mobility_scores(conn: sqlite3.Connection) -> Tuple[Dict[str, float], Dict[str, float]]:
    q = """
        SELECT 
            from_job_profile_id,
            to_job_profile_id,
            SUM(movement_count) AS total_movement_count,
            AVG(pct_total_movements) AS avg_pct_total_movements
        FROM analytics_movement_patterns
        GROUP BY from_job_profile_id, to_job_profile_id
    """
    df = pd.read_sql_query(q, conn)
    src: Dict[str, float] = {}
    tgt: Dict[str, float] = {}
    g1 = df.groupby("from_job_profile_id").agg(
        unique_dests=("to_job_profile_id", "nunique"),
        total_moves=("total_movement_count", "sum"),
        market_share=("avg_pct_total_movements", "mean"),
    )
    for job_id, row in g1.iterrows():
        diversity = min(float(row.unique_dests) / 10.0, 1.0)
        volume = min(float(row.total_moves) / 100.0, 1.0)
        market = min(float(row.market_share) * 10.0, 1.0) if pd.notna(row.market_share) else 0.0
        src[str(job_id)] = diversity * 50 + volume * 30 + market * 20
    g2 = df.groupby("to_job_profile_id").agg(
        unique_sources=("from_job_profile_id", "nunique"),
        total_moves=("total_movement_count", "sum"),
        market_share=("avg_pct_total_movements", "mean"),
    )
    for job_id, row in g2.iterrows():
        diversity = min(float(row.unique_sources) / 10.0, 1.0)
        volume = min(float(row.total_moves) / 100.0, 1.0)
        market = min(float(row.market_share) * 10.0, 1.0) if pd.notna(row.market_share) else 0.0
        tgt[str(job_id)] = diversity * 50 + volume * 30 + market * 20
    return src, tgt


def preload_monthlies(conn: sqlite3.Connection) -> Dict[Tuple[str, str], List[Tuple[str, int, int, float, float]]]:
    q = """
        SELECT movement_month, movement_count, unique_employees, avg_days_between, pct_total_movements,
               from_job_profile_id, to_job_profile_id
        FROM analytics_movement_patterns
        ORDER BY from_job_profile_id, to_job_profile_id, movement_month
    """
    rows = conn.execute(q).fetchall()
    bucket: Dict[Tuple[str, str], List[Tuple[str, int, int, float, float]]] = {}
    for (mm, mov, uniq, avgd, pct, f, t) in rows:
        key = (str(f), str(t))
        bucket.setdefault(key, []).append((mm, int(mov), int(uniq), float(avgd), float(pct) if pct is not None else 0.0))
    return bucket


def load_global_context(db_path: Path, recency_decay: float) -> GlobalContext:
    with sqlite3.connect(str(db_path)) as conn:
        jobs, fh = load_jobs_metadata(conn)
        src_mob, tgt_mob = calculate_mobility_scores(conn)
    return GlobalContext(jobs, fh, src_mob, tgt_mob, recency_decay)


# ---------------------------
# Realtime feature builder
# ---------------------------
def parse_level(x: Any) -> Optional[int]:
    try:
        return int(str(x).replace("Group ", "").replace("Group", ""))
    except Exception:
        return None


def build_realtime_features_for_pair(
    monthlies_index: Dict[Tuple[str, str], List[Tuple[str, int, int, float, float]]],
    ctx: GlobalContext,
    from_job: str,
    to_job: str,
) -> Optional[Dict[str, Any]]:
    from_meta = ctx.jobs_metadata.get(from_job)
    to_meta = ctx.jobs_metadata.get(to_job)
    if not from_meta or not to_meta:
        return None

    rows = monthlies_index.get((from_job, to_job), [])
    if rows:
        years = [int(r[0][:4]) for r in rows if r[0]]
        current_year = max(years)
        total_moves = 0
        total_unique = 0
        avg_days_list: List[float] = []
        avg_pct_list: List[float] = []
        recency_sum = 0.0
        for (mm, mov, uniq, avgd, pct) in rows:
            total_moves += mov
            total_unique += uniq
            if not math.isnan(avgd):
                avg_days_list.append(avgd)
            if pct is not None:
                avg_pct_list.append(pct)
            yr = int(mm[:4])
            years_ago = current_year - yr
            recency_sum += ctx.recency_decay ** float(years_ago)
        first_year = min(years)
        last_year = max(years)
        years_active = max(last_year - first_year + 1, 1)
        transition_frequency = len(rows)
        avg_days_between = sum(avg_days_list) / len(avg_days_list) if avg_days_list else 365.0
        avg_pct_total_movements = sum(avg_pct_list) / len(avg_pct_list) if avg_pct_list else 0.0
        recency_boost = (recency_sum / total_moves) if total_moves > 0 else 1.0
        observed = True
    else:
        total_moves = 0
        total_unique = 0
        years_active = 1
        transition_frequency = 0
        avg_days_between = 365.0
        avg_pct_total_movements = 0.0
        recency_sum = 0.0
        recency_boost = 1.0
        observed = False
        first_year = 0
        last_year = 0

    same_func = float(from_meta.get("JobFunction") == to_meta.get("JobFunction"))
    same_sub = float(from_meta.get("JobSubFunction") == to_meta.get("JobSubFunction"))
    same_level = float(from_meta.get("ManagementLevel") == to_meta.get("ManagementLevel"))
    same_cat = float(from_meta.get("JobCategory") == to_meta.get("JobCategory"))

    from_func_key = str(from_meta.get("JobFunction")) if from_meta.get("JobFunction") is not None else ""
    to_func_key = str(to_meta.get("JobFunction")) if to_meta.get("JobFunction") is not None else ""
    from_idx = ctx.function_hierarchy.get(from_func_key, 0)
    to_idx = ctx.function_hierarchy.get(to_func_key, 0)
    func_distance = float(abs(from_idx - to_idx))

    lvl_from = parse_level(from_meta.get("ManagementLevel"))
    lvl_to = parse_level(to_meta.get("ManagementLevel"))
    lvl_prog = float(lvl_to - lvl_from) if (lvl_from is not None and lvl_to is not None) else 0.0

    return {
        "total_movement_count": float(total_moves),
        "total_unique_employees": float(total_unique),
        "avg_days_between": float(avg_days_between),
        "avg_pct_total_movements": float(avg_pct_total_movements),
        "transition_frequency": float(transition_frequency),
        "years_active": float(years_active),
        "avg_movements_per_year": float(total_moves) / float(years_active),
        "recency_weighted_activity": float(recency_sum),
        "recency_boost": float(recency_boost),
        "has_observed_history": bool(observed),
        "source_mobility_score": float(ctx.source_mobility.get(from_job, 0.0)),
        "target_mobility_score": float(ctx.target_mobility.get(to_job, 0.0)),
        "same_job_function": same_func,
        "same_job_sub_function": same_sub,
        "same_management_level": same_level,
        "same_job_category": same_cat,
        "job_function_distance": func_distance,
        "management_level_progression": lvl_prog,
        "first_observed_year": float(first_year),
        "last_observed_year": float(last_year),
    }


# ---------------------------
# Gating & scoring
# ---------------------------
def movement_defaults_present(f: Dict[str, Any]) -> bool:
    return (
        f.get("total_movement_count", 0.0) == 0.0
        or f.get("avg_movements_per_year", 0.0) == 0.0
        or f.get("transition_frequency", 0.0) == 0.0
        or f.get("recency_weighted_activity", 0.0) == 0.0
        or f.get("recency_boost", 1.0) == 1.0
        or f.get("years_active", 1.0) == 1.0
        or f.get("avg_days_between", 365.0) == 365.0
    )


def passes_strict_evidence(f: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if not f.get("has_observed_history", False):
        return False, "NO_OBSERVED_HISTORY"
    if movement_defaults_present(f):
        return False, "MOVEMENT_DEFAULTS_PRESENT"
    if f.get("total_movement_count", 0.0) < MIN_TOTAL_MOVEMENTS:
        return False, "BELOW_MIN_TOTAL_MOVEMENTS"
    if f.get("transition_frequency", 0.0) < MIN_TRANSITION_MONTHS:
        return False, "BELOW_MIN_TRANSITION_MONTHS"
    if f.get("recency_weighted_activity", 0.0) < RWA_MIN:
        return False, "BELOW_MIN_RECENCY"
    if f.get("source_mobility_score", 0.0) < MIN_SOURCE_MOBILITY or f.get("target_mobility_score", 0.0) < MIN_TARGET_MOBILITY:
        return False, "MOBILITY_TOO_LOW"
    # Career progression sanity: allow +/-1 level; beyond requires strong evidence
    lvl_prog = float(f.get("management_level_progression", 0.0))
    if abs(lvl_prog) > MAX_LEVEL_JUMP_WITHOUT_STRONG_EVIDENCE:
        if not (
            f.get("total_movement_count", 0.0) >= STRONG_EVIDENCE_MOVES
            and f.get("transition_frequency", 0.0) >= STRONG_EVIDENCE_MONTHS
        ):
            return False, "LEVEL_JUMP_WEAK_EVIDENCE"
    return True, None


def insufficient_evidence(f: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if f.get("has_observed_history", False):
        reasons = []
        if f.get("total_movement_count", 0.0) < MIN_TOTAL_MOVEMENTS:
            reasons.append("BELOW_MIN_TOTAL_MOVEMENTS")
        if f.get("transition_frequency", 0.0) < MIN_TRANSITION_MONTHS:
            reasons.append("BELOW_MIN_TRANSITION_MONTHS")
        if f.get("recency_weighted_activity", 0.0) < RWA_MIN:
            reasons.append("BELOW_MIN_RECENCY")
        if reasons:
            return True, ";".join(reasons)
    return False, None


def calculate_feasibility_score(result: Dict[str, Any]) -> float:
    if result.get("assessment_status") in ("error", "low_feasibility", "insufficient_evidence"):
        return 0.0
    base_conf = result.get("confidence_score", 0.0)
    syn = result.get("synthetic_feature_percentage", 0.0)
    disagree = result.get("model_disagreement_std", 0.0)
    vol = result.get("predicted_annual_movements", 0.0)
    red = result.get("red_flags", [])

    # Base confidence
    confidence_factor = base_conf
    # Data quality factor
    if syn <= 0.5:
        dq = 1.0
    elif syn <= 0.85:
        dq = max(0.1, 1.0 - (syn - 0.5) * 2)
    else:
        dq = 0.05
    # Business logic factor
    bl = 0.3 if "CAREER_REVERSAL" in red else 1.0
    # Agreement factor
    if disagree <= 0.1:
        agree = 1.0
    elif disagree <= 0.3:
        agree = max(0.5, 1.0 - (disagree * 2))
    else:
        agree = 0.5
    # Volume factor (using recency-weighted proxy)
    if vol >= 0.5:
        volf = 1.0
    elif vol >= 0.3:
        volf = 0.8
    elif vol >= 0.1:
        volf = 0.4
    else:
        volf = 0.1

    score = confidence_factor * dq * bl * agree * volf
    return max(0.0, min(1.0, float(score)))


# ---------------------------
# Prediction & Assessment
# ---------------------------
def predict_pair(models: Dict[str, Any], feature_columns: List[str], feat: Dict[str, Any]) -> Tuple[Dict[str, Any], List[float]]:
    df = pd.DataFrame([feat])
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0.0
    X = df[feature_columns].copy()
    preds: List[float] = []
    model_breakdown: Dict[str, float] = {}
    for name, m in models.items():
        try:
            p = float(m.predict(X)[0])
            preds.append(p)
            model_breakdown[name] = p
        except Exception:
            continue
    return model_breakdown, preds


def assess_career_reversal(feat: Dict[str, Any]) -> Optional[str]:
    # Using level progression sign
    lvl_from = None
    lvl_to = None
    # Not available here; treat negative progression as demotion: from_level > to_level
    prog = feat.get("management_level_progression", 0.0)
    try:
        prog = float(prog)
    except Exception:
        prog = 0.0
    if prog < 0:
        # Demotion
        return "Management demotion detected"
    return None


# ---------------------------
# Main audit routine
# ---------------------------
def main() -> int:
    db_path = DEFAULT_DB_PATH
    models_dir = DEFAULT_MODELS_DIR

    # Load metadata/models/context
    feature_columns, recency_decay, model_files = load_model_metadata(models_dir)
    models = load_models(models_dir, model_files)

    with sqlite3.connect(str(db_path)) as conn:
        # In-use jobs (distinct JobProfileID in workforce_current)
        jobs_in_use = [
            str(r[0])
            for r in conn.execute(
                "SELECT DISTINCT JobProfileID FROM core_workforce_current WHERE JobProfileID IS NOT NULL"
            ).fetchall()
        ]
        # Global context and preloaded monthlies
        ctx = load_global_context(db_path, recency_decay)
        monthlies_index = preload_monthlies(conn)

    start_time = time.time()
    process = psutil.Process() if psutil else None
    mem_peak_mb = 0.0

    total_pairs = 0
    feasible_count = 0
    insufficient_count = 0
    not_feasible_count = 0
    errors_count = 0

    red_flag_counter = Counter()
    feasibility_counter = Counter()

    score_values: List[float] = []
    confidence_values: List[float] = []

    # Prediction spread diagnostics
    pred_all: List[float] = []
    pred_observed: List[float] = []
    pred_unseen: List[float] = []
    pred_feasible: List[float] = []
    pred_insufficient: List[float] = []
    pred_notfeasible: List[float] = []

    # Iterate full cartesian product excluding self
    pairs = [(f, t) for f in jobs_in_use for t in jobs_in_use if f != t]
    pbar = tqdm(pairs, desc="🔎 Auditing corpus", unit="pair")

    # For coverage summaries
    feasible_out_by_from: Dict[str, int] = defaultdict(int)
    feasible_in_by_to: Dict[str, int] = defaultdict(int)
    function_of: Dict[str, str] = {}
    # capture function labels
    # build once
    for jid, meta in ctx.jobs_metadata.items():
        function_of[jid] = str(meta.get("JobFunction")) if meta and meta.get("JobFunction") is not None else ""

    # Function pair acceptance tallies
    func_pair_totals: Dict[Tuple[str, str], int] = defaultdict(int)
    func_pair_feasible: Dict[Tuple[str, str], int] = defaultdict(int)

    for (from_job, to_job) in pbar:
        total_pairs += 1
        try:
            feat = build_realtime_features_for_pair(monthlies_index, ctx, from_job, to_job)
            if feat is None:
                not_feasible_count += 1
                red_flag_counter["MISSING_JOB_METADATA"] += 1
                feasibility_counter["LOW_FEASIBILITY"] += 1
                continue

            # Tally function pair totals
            ff = function_of.get(from_job, "")
            tf = function_of.get(to_job, "")
            func_pair_totals[(ff, tf)] += 1

            # Optionally compute model predictions for all pairs (diagnostics only)
            model_breakdown, preds = ({}, [])
            if RUN_PREDICTIONS_FOR_ALL_PAIRS:
                try:
                    model_breakdown, preds = predict_pair(models, feature_columns, feat)
                    if preds:
                        ensemble_prediction_all = float(np.mean(preds))
                        pred_all.append(ensemble_prediction_all)
                        if feat.get("has_observed_history", False):
                            pred_observed.append(ensemble_prediction_all)
                        else:
                            pred_unseen.append(ensemble_prediction_all)
                except Exception:
                    # swallow diagnostics prediction errors
                    pass

            # Strict fail-fast
            ok, reason = passes_strict_evidence(feat)
            if not ok:
                not_feasible_count += 1
                if reason:
                    red_flag_counter[reason] += 1
                feasibility_counter["LOW_FEASIBILITY"] += 1
                if RUN_PREDICTIONS_FOR_ALL_PAIRS and preds:
                    pred_notfeasible.append(float(np.mean(preds)))
                continue

            # Insufficient evidence category (observed but below volume/recency)
            ie, ie_reason = insufficient_evidence(feat)
            if ie:
                insufficient_count += 1
                if ie_reason:
                    red_flag_counter[ie_reason] += 1
                feasibility_counter["INSUFFICIENT_EVIDENCE"] += 1
                if RUN_PREDICTIONS_FOR_ALL_PAIRS and preds:
                    pred_insufficient.append(float(np.mean(preds)))
                continue

            # At this point, we have sufficient evidence → run models
            model_breakdown, preds = predict_pair(models, feature_columns, feat)
            if not preds:
                errors_count += 1
                red_flag_counter["MODEL_PREDICTION_FAILED"] += 1
                feasibility_counter["ERROR"] += 1
                continue

            ensemble_prediction = float(np.mean(preds))
            prediction_std = float(np.std(preds))
            prediction_mean = float(np.mean(preds))
            cov = float(prediction_std / (prediction_mean + 1e-6))
            confidence = float(max(0.0, min(1.0, 1.0 - cov)))

            # Career reversal red flag
            reversal = assess_career_reversal(feat)
            red_flags: List[str] = []
            if reversal:
                red_flags.append("CAREER_REVERSAL")
                red_flag_counter["CAREER_REVERSAL"] += 1

            # Construct result dict for scoring
            res = {
                "assessment_status": "success",
                "confidence_score": confidence,
                "synthetic_feature_percentage": 0.0,  # strict evidence should imply near-zero movement defaults
                "model_disagreement_std": prediction_std,
                "predicted_annual_movements": ensemble_prediction,
                "red_flags": red_flags,
            }
            score = calculate_feasibility_score(res)
            score_values.append(score)
            confidence_values.append(confidence)

            feasible_count += 1
            feasibility_counter["HIGH_OR_MODERATE"] += 1
            pred_feasible.append(ensemble_prediction)
            feasible_out_by_from[from_job] += 1
            feasible_in_by_to[to_job] += 1
            func_pair_feasible[(ff, tf)] += 1

        except Exception:
            errors_count += 1
            red_flag_counter["PROCESSING_ERROR"] += 1
            feasibility_counter["ERROR"] += 1
            continue

        # track memory peak
        if process:
            try:
                mem_mb = process.memory_info().rss / (1024 * 1024)
                if mem_mb > mem_peak_mb:
                    mem_peak_mb = mem_mb
            except Exception:
                pass

    # ---------------------------
    # Summary Report
    # ---------------------------
    elapsed = time.time() - start_time
    print("\n📊 CORPUS FEASIBILITY AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total in-use jobs:         {len(jobs_in_use):,}")
    print(f"Total pairs evaluated:     {total_pairs:,}")
    print(f"Feasible (passed gates):   {feasible_count:,} ({(feasible_count/total_pairs)*100:.1f}%)")
    print(f"Insufficient Evidence:     {insufficient_count:,} ({(insufficient_count/total_pairs)*100:.1f}%)")
    print(f"Not Feasible (fail-fast):  {not_feasible_count:,} ({(not_feasible_count/total_pairs)*100:.1f}%)")
    print(f"Errors:                    {errors_count:,} ({(errors_count/total_pairs)*100:.1f}%)")
    print(f"⏱️  Runtime:                {elapsed:.1f}s  |  Throughput: {total_pairs/elapsed:.1f} pairs/s")
    if mem_peak_mb > 0:
        print(f"🧠 Peak RSS:               {mem_peak_mb:.1f} MB")

    if score_values:
        print("\n💯 Feasibility Score (passed gates only)")
        print(f"   Min: {min(score_values):.3f}, Max: {max(score_values):.3f}, "
              f"Mean: {float(np.mean(score_values)):.3f}, Median: {float(np.median(score_values)):.3f}")
    if confidence_values:
        print("\n🎲 Confidence (passed gates only)")
        print(f"   Min: {min(confidence_values):.3f}, Max: {max(confidence_values):.3f}, "
              f"Mean: {float(np.mean(confidence_values)):.3f}, Median: {float(np.median(confidence_values)):.3f}")

    if feasibility_counter:
        print("\n🎯 Outcome Categories:")
        total = sum(feasibility_counter.values())
        for k, v in feasibility_counter.most_common():
            print(f"   • {k}: {v:,} ({(v/total)*100:.1f}%)")

    if red_flag_counter:
        print("\n🚨 Red Flags (Top 12):")
        for k, v in red_flag_counter.most_common(12):
            print(f"   • {k}: {v:,}")

    print("=" * 80)
    # Prediction spread diagnostics
    def print_dist(label: str, values: List[float]):
        if not values:
            return
        q = np.quantile(values, [0.0, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0])
        print(f"\n📈 Prediction spread — {label}")
        print(f"   Count: {len(values):,}")
        print(f"   Min/Median/Max: {q[0]:.3f} / {q[1]:.3f} / {q[-1]:.3f}")
        print(f"   P75/P90/P95/P99: {q[2]:.3f} / {q[3]:.3f} / {q[4]:.3f} / {q[5]:.3f}")

    if RUN_PREDICTIONS_FOR_ALL_PAIRS:
        print_dist("All pairs", pred_all)
        print_dist("Observed pairs", pred_observed)
        print_dist("Unseen pairs", pred_unseen)
        print_dist("Feasible (passed gates)", pred_feasible)
        print_dist("Insufficient Evidence", pred_insufficient)
        print_dist("Not Feasible (fail-fast)", pred_notfeasible)

    # --------------
    # Coverage by role
    # --------------
    # We need counts of feasible outgoings/incomings by role; for performance, track on-the-fly
    if feasible_out_by_from:
        out_counts = np.array(list(feasible_out_by_from.values()), dtype=float)
        print("\n👥 Feasible outgoing per from_job (distribution)")
        print(f"   Min: {out_counts.min():.0f}, P25: {np.quantile(out_counts, 0.25):.0f}, "
              f"Median: {np.median(out_counts):.0f}, P75: {np.quantile(out_counts, 0.75):.0f}, Max: {out_counts.max():.0f}")
        num_zero_out = sum(1 for v in out_counts if v == 0)
        print(f"   Roles with zero feasible outgoing: {num_zero_out:,}")
    if feasible_in_by_to:
        in_counts = np.array(list(feasible_in_by_to.values()), dtype=float)
        print("\n🏁 Feasible incoming per to_job (distribution)")
        print(f"   Min: {in_counts.min():.0f}, P25: {np.quantile(in_counts, 0.25):.0f}, "
              f"Median: {np.median(in_counts):.0f}, P75: {np.quantile(in_counts, 0.75):.0f}, Max: {in_counts.max():.0f}")
        num_zero_in = sum(1 for v in in_counts if v == 0)
        print(f"   Roles with zero feasible incoming: {num_zero_in:,}")

    # Function pair acceptance
    if func_pair_totals:
        print("\n🧭 Function-pair feasible rates (top 20 by total)")
        rows = []
        for (ff, tf), tot in func_pair_totals.items():
            feas = func_pair_feasible.get((ff, tf), 0)
            rate = (feas / tot) if tot > 0 else 0.0
            rows.append((ff, tf, tot, feas, rate))
        rows.sort(key=lambda r: r[2], reverse=True)
        for ff, tf, tot, feas, rate in rows[:20]:
            print(f"   • {ff} → {tf}: {feas:,}/{tot:,} ({rate*100:.1f}%)")

    # Near-miss diagnostics
    # RWA within 10%, counts within 1 of thresholds
    # Note: For performance we did not retain per-pair values here; consider adding streaming export if needed.
    print("\n💡 Tip: enable streaming CSV export if you want near-miss pair lists (RWA within 10%, count within 1)")

    print("✅ Audit complete")
    print("✅ Audit complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


