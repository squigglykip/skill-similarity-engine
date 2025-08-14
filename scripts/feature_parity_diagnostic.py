#!/usr/bin/env python3
"""
Real-time Feature Parity Diagnostic
===================================

Purpose:
- Baseline whether the real-time feature engineering can produce the exact
  feature columns required by the trained joblib models (from model_metadata.json)
- Quantify feature health and completeness before calling models
- Highlight top missing columns and synthetic/default-heavy cases

What it does:
1) Loads training feature_columns and recency_decay_rate from model metadata
2) Connects to the SQLite database and loads minimal global context:
   - jobs metadata (core_job_architecture)
   - mobility scores (aggregated from analytics_movement_patterns)
3) Samples job pairs (observed + random) and builds real-time features per pair
4) Compares produced features vs training columns; computes diagnostics:
   - has_observed_history
   - missing_columns_count and list
   - synthetic_feature_percentage (same indicators as runtime)
5) Prints a concise summary and optionally exports CSV/JSON diagnostics

Usage (PowerShell):
  python scripts/feature_parity_diagnostic.py \
    --database models/2025-Q3/business_context.sqlite \
    --models-dir models/2025-Q3 \
    --sample-size 500 \
    --format console

Optional exports:
  --format json --output diagnostics.json
  --format csv  --output diagnostics.csv
"""

import argparse
import json
import random
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def load_model_metadata(models_dir: str) -> Tuple[List[str], float]:
    """Load training feature_columns and recency_decay_rate from model_metadata.json."""
    candidate_paths = [
        Path(models_dir) / "model_metadata.json",
        Path(models_dir) / "ml-training-metadata.json",
        Path("ml-training-metadata.json"),
    ]
    metadata_path = next((p for p in candidate_paths if p.exists()), None)
    if not metadata_path:
        raise FileNotFoundError(f"Model metadata not found in: {candidate_paths}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    feature_columns = metadata.get("feature_columns", [])
    recency_decay = (
        metadata.get("ml_config", {}).get("recency_decay_rate", 0.4)
        if isinstance(metadata.get("ml_config"), dict)
        else 0.4
    )
    return feature_columns, float(recency_decay)


def load_jobs_metadata(conn: sqlite3.Connection) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int]]:
    """Load jobs metadata and job function hierarchy mapping."""
    query = """
        SELECT JobProfileID, JobProfile, JobFunction, JobSubFunction,
               ManagementLevel, JobCategory
        FROM core_job_architecture
        ORDER BY JobProfile
    """
    jobs_df = pd.read_sql_query(query, conn)
    jobs_metadata: Dict[str, Dict[str, Any]] = {}
    for _, row in jobs_df.iterrows():
        jobs_metadata[str(row["JobProfileID"])] = {
            "JobProfile": row["JobProfile"],
            "JobFunction": row["JobFunction"],
            "JobSubFunction": row["JobSubFunction"],
            "ManagementLevel": row["ManagementLevel"],
            "JobCategory": row["JobCategory"],
        }
    job_functions = sorted(jobs_df["JobFunction"].dropna().unique())
    function_hierarchy = {func: idx for idx, func in enumerate(job_functions)}
    return jobs_metadata, function_hierarchy


def calculate_mobility_scores(conn: sqlite3.Connection) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Calculate source/target mobility scores from analytics_movement_patterns."""
    mobility_query = """
        SELECT 
            from_job_profile_id,
            to_job_profile_id,
            SUM(movement_count) AS total_movement_count,
            AVG(pct_total_movements) AS avg_pct_total_movements
        FROM analytics_movement_patterns
        GROUP BY from_job_profile_id, to_job_profile_id
    """
    df = pd.read_sql_query(mobility_query, conn)

    source_scores: Dict[str, float] = {}
    target_scores: Dict[str, float] = {}

    source_group = df.groupby("from_job_profile_id").agg(
        unique_dests=("to_job_profile_id", "nunique"),
        total_moves=("total_movement_count", "sum"),
        market_share=("avg_pct_total_movements", "mean"),
    )
    for job_id, row in source_group.iterrows():
        diversity = min(float(row.unique_dests) / 10.0, 1.0)
        volume = min(float(row.total_moves) / 100.0, 1.0)
        market = min(float(row.market_share) * 10.0, 1.0) if pd.notna(row.market_share) else 0.0
        source_scores[str(job_id)] = diversity * 50 + volume * 30 + market * 20

    target_group = df.groupby("to_job_profile_id").agg(
        unique_sources=("from_job_profile_id", "nunique"),
        total_moves=("total_movement_count", "sum"),
        market_share=("avg_pct_total_movements", "mean"),
    )
    for job_id, row in target_group.iterrows():
        diversity = min(float(row.unique_sources) / 10.0, 1.0)
        volume = min(float(row.total_moves) / 100.0, 1.0)
        market = min(float(row.market_share) * 10.0, 1.0) if pd.notna(row.market_share) else 0.0
        target_scores[str(job_id)] = diversity * 50 + volume * 30 + market * 20

    return source_scores, target_scores


def query_pair_monthlies(
    conn: sqlite3.Connection, from_job: str, to_job: str
) -> List[Tuple[str, int, int, float, float]]:
    """Return monthly rows for a pair: (movement_month, movement_count, unique_employees, avg_days_between, pct_total_movements)."""
    sql = """
        SELECT movement_month, movement_count, unique_employees, avg_days_between, pct_total_movements
        FROM analytics_movement_patterns
        WHERE from_job_profile_id = ? AND to_job_profile_id = ?
        ORDER BY movement_month
    """
    return conn.execute(sql, (from_job, to_job)).fetchall()


def build_realtime_features(
    conn: sqlite3.Connection,
    jobs_meta: Dict[str, Dict[str, Any]],
    func_hierarchy: Dict[str, int],
    src_mobility: Dict[str, float],
    tgt_mobility: Dict[str, float],
    recency_decay: float,
    from_job: str,
    to_job: str,
) -> Optional[Dict[str, Any]]:
    """Build the real-time feature dict for a job pair."""
    from_meta = jobs_meta.get(from_job)
    to_meta = jobs_meta.get(to_job)
    if not from_meta or not to_meta:
        return None

    rows = query_pair_monthlies(conn, from_job, to_job)
    if rows:
        years = [int(r[0][:4]) for r in rows if r[0]]
        current_year = max(years) if years else 0
        total_moves = 0
        total_unique = 0
        avg_days_list: List[float] = []
        avg_pct_list: List[float] = []
        recency_sum = 0.0
        for (mm, mov, uniq, avg_days, pct) in rows:
            total_moves += int(mov)
            total_unique += int(uniq)
            if pd.notna(avg_days):
                avg_days_list.append(float(avg_days))
            if pd.notna(pct):
                avg_pct_list.append(float(pct))
            yr = int(mm[:4])
            years_ago = current_year - yr
            recency_sum += float(recency_decay) ** float(years_ago)

        first_year = min(years) if years else current_year
        last_year = max(years) if years else current_year
        years_active = max(last_year - first_year + 1, 1)
        transition_freq = len(rows)
        avg_days_between = sum(avg_days_list) / len(avg_days_list) if avg_days_list else 365.0
        avg_pct_total_movements = sum(avg_pct_list) / len(avg_pct_list) if avg_pct_list else 0.0
        recency_boost = (recency_sum / total_moves) if total_moves > 0 else 1.0
        has_observed_history = True
    else:
        total_moves = 0
        total_unique = 0
        years_active = 1
        transition_freq = 0
        avg_days_between = 365.0
        avg_pct_total_movements = 0.0
        recency_sum = 0.0
        recency_boost = 1.0
        has_observed_history = False

    # Architecture booleans
    same_func = float(from_meta.get("JobFunction") == to_meta.get("JobFunction"))
    same_sub = float(from_meta.get("JobSubFunction") == to_meta.get("JobSubFunction"))
    same_level = float(from_meta.get("ManagementLevel") == to_meta.get("ManagementLevel"))
    same_cat = float(from_meta.get("JobCategory") == to_meta.get("JobCategory"))

    # Function distance
    from_idx = func_hierarchy.get(from_meta.get("JobFunction"), 0)
    to_idx = func_hierarchy.get(to_meta.get("JobFunction"), 0)
    func_distance = float(abs(from_idx - to_idx))

    # Management level progression
    def _parse_level(x: Any) -> Optional[int]:
        try:
            return int(str(x).replace("Group ", "").replace("Group", ""))
        except Exception:
            return None

    lvl_from = _parse_level(from_meta.get("ManagementLevel"))
    lvl_to = _parse_level(to_meta.get("ManagementLevel"))
    lvl_prog = float(lvl_to - lvl_from) if (lvl_from is not None and lvl_to is not None) else 0.0

    features: Dict[str, Any] = {
        # Movement features
        "total_movement_count": float(total_moves),
        "total_unique_employees": float(total_unique),
        "avg_days_between": float(avg_days_between),
        "avg_pct_total_movements": float(avg_pct_total_movements),
        "transition_frequency": float(transition_freq),
        "years_active": float(years_active),
        "avg_movements_per_year": float(total_moves) / float(years_active),
        "recency_weighted_activity": float(recency_sum),
        "recency_boost": float(recency_boost),
        "has_observed_history": bool(has_observed_history),
        # Mobility
        "source_mobility_score": float(src_mobility.get(from_job, 0.0)),
        "target_mobility_score": float(tgt_mobility.get(to_job, 0.0)),
        # Architecture
        "same_job_function": same_func,
        "same_job_sub_function": same_sub,
        "same_management_level": same_level,
        "same_job_category": same_cat,
        "job_function_distance": func_distance,
        "management_level_progression": lvl_prog,
    }
    return features


def synthetic_percentage(feature_values: Dict[str, Any]) -> float:
    """Compute synthetic/default indicator percentage aligned to runtime logic."""
    indicators = [
        feature_values.get("total_movement_count", 0) == 0,
        feature_values.get("avg_movements_per_year", 0) == 0,
        feature_values.get("transition_frequency", 0) == 0,
        feature_values.get("recency_weighted_activity", 0) == 0,
        feature_values.get("recency_boost", 1) == 1,
        feature_values.get("avg_days_between", 365) == 365,
        feature_values.get("years_active", 1) == 1,
        feature_values.get("source_mobility_score", 0) == 0,
        feature_values.get("target_mobility_score", 0) == 0,
    ]
    total = len(indicators)
    return float(sum(indicators)) / float(total) if total else 0.0


def sample_job_pairs(
    conn: sqlite3.Connection, jobs_meta: Dict[str, Dict[str, Any]], sample_size: int
) -> List[Tuple[str, str]]:
    """Half observed pairs, half random pairs (excluding self transitions)."""
    # Observed pairs from analytics_movement_patterns
    observed_df = pd.read_sql_query(
        """
        SELECT DISTINCT from_job_profile_id AS from_id, to_job_profile_id AS to_id
        FROM analytics_movement_patterns
        WHERE from_job_profile_id IS NOT NULL AND to_job_profile_id IS NOT NULL
        """,
        conn,
    )
    observed_pairs = list(
        {(str(r.from_id), str(r.to_id)) for _, r in observed_df.iterrows() if str(r.from_id) != str(r.to_id)}
    )
    random.shuffle(observed_pairs)

    job_ids = list(jobs_meta.keys())
    random_pairs: List[Tuple[str, str]] = []
    tries = 0
    max_tries = sample_size * 10
    while len(random_pairs) < sample_size // 2 and tries < max_tries:
        f = random.choice(job_ids)
        t = random.choice(job_ids)
        if f != t and (f, t) not in observed_pairs:
            random_pairs.append((f, t))
        tries += 1

    out: List[Tuple[str, str]] = []
    out.extend(observed_pairs[: sample_size // 2])
    out.extend(random_pairs)
    # If still short, pad with more observed
    if len(out) < sample_size:
        out.extend(observed_pairs[sample_size // 2 : sample_size])
    return out[:sample_size]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Real-time Feature Parity Diagnostic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/feature_parity_diagnostic.py --database models/2025-Q3/business_context.sqlite --models-dir models/2025-Q3 --sample-size 500
  python scripts/feature_parity_diagnostic.py --database models/2025-Q3/business_context.sqlite --models-dir models/2025-Q3 --format json --output diagnostics.json
        """,
    )
    parser.add_argument("--database", required=True, help="Path to SQLite database")
    parser.add_argument("--models-dir", required=True, help="Directory containing model metadata")
    parser.add_argument("--sample-size", type=int, default=500, help="Number of job pairs to analyze (default: 500)")
    parser.add_argument(
        "--format",
        choices=["console", "json", "csv"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument("--output", help="Output file path for json/csv (optional)")

    args = parser.parse_args()

    try:
        feature_columns, recency_decay = load_model_metadata(args.models_dir)
        with sqlite3.connect(args.database) as conn:
            jobs_meta, func_hierarchy = load_jobs_metadata(conn)
            src_mobility, tgt_mobility = calculate_mobility_scores(conn)

            pairs = sample_job_pairs(conn, jobs_meta, args.sample_size)

            diagnostics: List[Dict[str, Any]] = []
            missing_counter = Counter()
            synthetic_values: List[float] = []
            seen_count = 0
            unseen_count = 0

            for from_job, to_job in pairs:
                feat = build_realtime_features(
                    conn,
                    jobs_meta,
                    func_hierarchy,
                    src_mobility,
                    tgt_mobility,
                    recency_decay,
                    from_job,
                    to_job,
                )
                if feat is None:
                    # Missing job metadata
                    diagnostics.append(
                        {
                            "from_job": from_job,
                            "to_job": to_job,
                            "has_observed_history": False,
                            "missing_feature_columns_count": len(feature_columns),
                            "missing_feature_columns": feature_columns,
                            "synthetic_feature_percentage": 1.0,
                            "notes": "Missing job metadata for one or both roles",
                        }
                    )
                    continue

                has_history = bool(feat.get("has_observed_history", False))
                seen_count += 1 if has_history else 0
                unseen_count += 0 if has_history else 1

                # Determine missing training columns
                feat_cols = set(feat.keys())
                required = set(feature_columns)
                missing = sorted(list(required - feat_cols))
                for col in missing:
                    missing_counter[col] += 1

                syn_pct = synthetic_percentage(feat)
                synthetic_values.append(syn_pct)

                diagnostics.append(
                    {
                        "from_job": from_job,
                        "to_job": to_job,
                        "has_observed_history": has_history,
                        "missing_feature_columns_count": len(missing),
                        "missing_feature_columns": missing,
                        "synthetic_feature_percentage": syn_pct,
                        "source_mobility_score": feat.get("source_mobility_score", 0.0),
                        "target_mobility_score": feat.get("target_mobility_score", 0.0),
                    }
                )

            # Summary
            total = len(diagnostics)
            complete = sum(1 for d in diagnostics if d["missing_feature_columns_count"] == 0)
            lt5_missing = sum(1 for d in diagnostics if 0 < d["missing_feature_columns_count"] <= 5)
            ge20pct_missing = sum(
                1
                for d in diagnostics
                if d["missing_feature_columns_count"] / max(1, len(feature_columns)) >= 0.2
            )

            summary = {
                "total_pairs_analyzed": total,
                "observed_pairs": seen_count,
                "unseen_pairs": unseen_count,
                "feature_columns_required": len(feature_columns),
                "pairs_with_all_features": complete,
                "pairs_with_<=5_missing": lt5_missing,
                "pairs_with_>=20pct_missing": ge20pct_missing,
                "synthetic_feature_stats": {
                    "min": float(np.min(synthetic_values)) if synthetic_values else 0.0,
                    "max": float(np.max(synthetic_values)) if synthetic_values else 0.0,
                    "mean": float(np.mean(synthetic_values)) if synthetic_values else 0.0,
                    "median": float(np.median(synthetic_values)) if synthetic_values else 0.0,
                    "std": float(np.std(synthetic_values)) if synthetic_values else 0.0,
                },
                "most_frequently_missing_columns": [
                    {"column": col, "count": cnt} for col, cnt in missing_counter.most_common(15)
                ],
            }

            if args.format == "console":
                print("\n🔬 REAL-TIME FEATURE PARITY DIAGNOSTIC")
                print("=" * 80)
                print(f"📊 Total pairs analyzed: {summary['total_pairs_analyzed']:,}")
                print(f"   • Observed pairs: {summary['observed_pairs']:,}")
                print(f"   • Unseen pairs:   {summary['unseen_pairs']:,}")
                print(f"📋 Training feature columns required: {summary['feature_columns_required']:,}")
                print(f"✅ Pairs with all features present: {summary['pairs_with_all_features']:,}")
                print(f"🟡 Pairs with ≤5 missing columns:   {summary['pairs_with_<=5_missing']:,}")
                print(f"🔴 Pairs with ≥20% columns missing: {summary['pairs_with_>=20pct_missing']:,}")
                print("\n🔬 Synthetic Feature Percentage (0-1)")
                s = summary["synthetic_feature_stats"]
                print(f"   • Min: {s['min']:.3f}, Max: {s['max']:.3f}, Mean: {s['mean']:.3f}, Median: {s['median']:.3f}, Std: {s['std']:.3f}")
                if summary["most_frequently_missing_columns"]:
                    print("\n🚨 Top Missing Training Columns:")
                    for item in summary["most_frequently_missing_columns"]:
                        print(f"   • {item['column']}: {item['count']:,} pairs")
                print("=" * 80)

            elif args.format == "json":
                payload = {"summary": summary, "diagnostics": diagnostics}
                if not args.output:
                    print(json.dumps(payload, indent=2, default=str))
                else:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2, default=str)
                    print(f"💾 Saved JSON to {args.output}")

            elif args.format == "csv":
                df = pd.DataFrame(diagnostics)
                if not args.output:
                    # Print first 20 rows to console
                    print(df.head(20).to_csv(index=False))
                else:
                    df.to_csv(args.output, index=False)
                    print(f"💾 Saved CSV to {args.output}")

            return 0

    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


