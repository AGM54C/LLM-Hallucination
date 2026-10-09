"""Verify the reused workbook against the lab table and enumerate matched contrasts.

Molecule-name crosswalks are inferred from globally unique measured-yield anchors
and then checked against ALL 3955 four-factor conditions. This is a provenance
join, not a chemical canonicalizer or a predictive model.
"""
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
import random
import pandas as pd

ROOT = Path(__file__).resolve().parent
MAP = {"Ligand": "ligand", "Additive": "additive", "Base": "base", "Aryl halide": "aryl_halide"}

def main():
    canonical = pd.read_csv(ROOT / "buchwald_hartwig_canonical.csv")
    raw = pd.read_csv(ROOT / "doyle_CN_raw.csv")
    raw["source_raw_csv_row"] = raw.index + 2
    counts_a = canonical["Output"].value_counts()
    counts_b = raw["yield"].value_counts()
    unique = set(counts_a[counts_a == 1].index) & set(counts_b[counts_b == 1].index)
    anchor = raw[raw["yield"].isin(unique)].set_index("yield")
    mapping = {factor: defaultdict(set) for factor in MAP}
    anchor_counts = {factor: defaultdict(int) for factor in MAP}
    for _, row in canonical[canonical["Output"].isin(unique)].iterrows():
        other = anchor.loc[row["Output"]]
        for factor, name in MAP.items():
            mapping[factor][row[factor]].add(other[name])
            anchor_counts[factor][row[factor]] += 1
    for factor in MAP:
        assert set(mapping[factor]) == set(canonical[factor]), factor
        assert all(len(names) == 1 for names in mapping[factor].values()), factor
    lookup = raw.set_index(list(MAP.values()), drop=False)
    assert not lookup.index.duplicated().any()
    crosswalk = []
    for _, row in canonical.iterrows():
        key = tuple(next(iter(mapping[f][row[f]])) for f in MAP)
        original = lookup.loc[key]
        difference = abs(float(row["Output"]) - float(original["yield"]))
        assert difference < 1e-7, (key, difference)
        combined = {"condition_id": row["condition_id"], "workbook_sheet": row["source_sheet"],
                    "workbook_excel_row": int(row["source_excel_row"]),
                    **original.to_dict(), "workbook_Output": row["Output"], "absolute_yield_difference": difference}
        crosswalk.append(combined)
    annotated = pd.DataFrame(crosswalk)
    annotated.to_csv(ROOT / "buchwald_hartwig_annotated.csv", index=False)
    included = set(annotated["source_raw_csv_row"])
    excluded = raw[~raw["source_raw_csv_row"].isin(included)].copy()
    excluded.to_csv(ROOT / "lab_rows_not_in_reused_workbook.csv", index=False)
    audit = {
        "raw_rows": len(raw), "raw_columns": list(raw.columns),
        "raw_missing_by_column": raw.isna().sum().to_dict(),
        "plate_row_counts": raw["plate"].value_counts().sort_index().to_dict(),
        "raw_duplicate_plate_well": int(raw.duplicated(["plate", "row", "col"]).sum()),
        "raw_duplicate_factor_condition": int(raw.duplicated(list(MAP.values())).sum()),
        "matched_workbook_rows": len(annotated), "globally_unique_yield_anchor_rows": len(unique),
        "all_matches_unique": len(included) == len(annotated),
        "maximum_yield_difference": float(annotated["absolute_yield_difference"].max()),
        "excluded_raw_rows": len(excluded),
        "excluded_additive_counts": excluded["additive"].fillna("<missing / no additive>").value_counts().to_dict(),
        "raw_named_additives": int(raw["additive"].nunique()),
        "additive_plate_counts": raw.dropna(subset=["additive"]).groupby("additive")["plate"].nunique().to_dict(),
        "critical_interpretation": "Each named additive occurs on one plate only: comparisons across such additives can also change plate. The table alone cannot separate additive effects from plate effects.",
        "name_crosswalk": {f: {s: {"name": next(iter(names)), "unique_yield_anchors": anchor_counts[f][s]}
                                for s, names in entries.items()} for f, entries in mapping.items()},
    }
    (ROOT / "lab_crosswalk_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    interactions = []
    complete_counts = {}
    for variable, fixed in [("aryl_halide", ["base", "additive"]), ("additive", ["base", "aryl_halide"])]:
        complete_counts[variable] = 0
        for fixed_values, group in annotated.groupby(fixed, sort=True):
            cells = {(row["ligand"], row[variable]): row for _, row in group.iterrows()}
            for ligand_a, ligand_b in combinations(sorted(group["ligand"].unique()), 2):
                for context_a, context_b in combinations(sorted(group[variable].unique()), 2):
                    keys = [(ligand_a, context_a), (ligand_b, context_a),
                            (ligand_a, context_b), (ligand_b, context_b)]
                    if not all(k in cells for k in keys):
                        continue
                    rows = [cells[k] for k in keys]
                    if len({r["plate"] for r in rows}) != 1:
                        continue
                    complete_counts[variable] += 1
                    yaa, yba, yab, ybb = [float(r["yield"]) for r in rows]
                    delta_a, delta_b = yba - yaa, ybb - yab
                    if not ((delta_a >= 15 and delta_b <= -15) or (delta_a <= -15 and delta_b >= 15)):
                        continue
                    interactions.append({
                        "varying_context": variable, **dict(zip(fixed, fixed_values)),
                        "plate": int(rows[0]["plate"]), "ligand_a": ligand_a, "ligand_b": ligand_b,
                        "context_a": context_a, "context_b": context_b,
                        "row_AA": rows[0]["condition_id"], "row_BA": rows[1]["condition_id"],
                        "row_AB": rows[2]["condition_id"], "row_BB": rows[3]["condition_id"],
                        "yield_AA": yaa, "yield_BA": yba, "yield_AB": yab, "yield_BB": ybb,
                        "delta_at_context_a_pp": delta_a, "delta_at_context_b_pp": delta_b,
                        "difference_in_differences_pp": delta_b - delta_a,
                    })
    pd.DataFrame(interactions).to_csv(ROOT / "within_plate_rank_reversal_candidates.csv", index=False)
    rng = random.Random(20261004)
    examples = {}
    counts = {}
    for variable in complete_counts:
        pool = [x for x in interactions if x["varying_context"] == variable]
        counts[variable] = len(pool)
        examples[variable] = rng.sample(pool, min(2, len(pool)))
    selection = {
        "source": "Real measured yields, never selected using model responses",
        "criterion": "Complete same-plate 2x2 quartet; ligand contrast >= +15 pp in one context and <= -15 pp in the other",
        "threshold_interpretation": "Descriptive contrast threshold, NOT a statistical significance or reproducibility threshold",
        "complete_same_plate_quartets": complete_counts,
        "qualifying_quartets": counts,
        "illustration_sampling": "2 examples per context, Python random.Random(20261004), from all qualifying quartets",
        "examples": examples,
        "sampling_unit_warning": "Quartets share measurement rows and are not independent experimental replicates; split and infer at context/group level.",
    }
    (ROOT / "interaction_examples.json").write_text(json.dumps(selection, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"raw_rows": len(raw), "matched": len(annotated), "excluded": len(excluded),
                      "anchors": len(unique), "maximum_yield_difference": audit["maximum_yield_difference"],
                      "excluded_additives": audit["excluded_additive_counts"],
                      "complete_quartets": complete_counts, "qualifying": counts,
                      "examples": examples}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
