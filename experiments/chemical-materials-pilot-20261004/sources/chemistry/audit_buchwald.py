"""Read-only audit of downloaded experimental workbook; derive one canonical CSV."""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "Dreher_and_Doyle_input_data.xlsx"
FACTORS = ["Ligand", "Additive", "Base", "Aryl halide"]

def row_multiset(frame):
    return Counter(tuple(row) for row in frame.itertuples(index=False, name=None))

def main():
    sheets = pd.read_excel(SOURCE, sheet_name=None, keep_default_na=False)
    reference = sheets["FullCV_01"]
    reference_set = row_multiset(reference)
    report = {"source_filename": SOURCE.name,
              "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "canonical_sheet": "FullCV_01", "sheets": {}}
    for name, frame in sheets.items():
        report["sheets"][name] = {
            "rows": len(frame), "columns": list(frame.columns),
            "blank_cells": {c: int(frame[c].eq("").sum()) for c in frame},
            "duplicate_full_rows": int(frame.duplicated().sum()),
            "duplicate_condition_rows": int(frame.duplicated(FACTORS).sum()),
            "same_row_multiset_as_canonical": row_multiset(frame) == reference_set,
        }
    levels = {c: sorted(reference[c].unique().tolist()) for c in FACTORS}
    observed = set(reference[FACTORS].itertuples(index=False, name=None))
    missing = sorted(set(itertools.product(*(levels[c] for c in FACTORS))) - observed)
    output = pd.to_numeric(reference["Output"], errors="coerce")
    report.update({
        "factor_unique_counts": {c: len(v) for c, v in levels.items()},
        "factor_values": levels,
        "observed_unique_condition_count": len(observed),
        "cartesian_grid_size": len(observed) + len(missing),
        "unobserved_grid_conditions": len(missing),
        "output": {"numeric_count": int(output.notna().sum()),
                   "nonnumeric_count": int(output.isna().sum()),
                   "minimum": float(output.min()), "maximum": float(output.max()),
                   "zero_count": int(output.eq(0).sum()), "negative_count": int(output.lt(0).sum()),
                   "above_100_count": int(output.gt(100).sum()),
                   "quantiles": {str(k): float(v) for k, v in output.quantile([0,.25,.5,.75,1]).items()}},
        "replicates": "No independent replicate ID exists in this workbook. Identical rows across sheets are not replicate experiments.",
    })
    canonical = reference.copy()
    canonical.insert(0, "source_excel_row", range(2, len(canonical) + 2))
    canonical.insert(0, "source_sheet", "FullCV_01")
    keys = [hashlib.sha256(json.dumps(list(row), ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()[:16]
            for row in reference[FACTORS].itertuples(index=False, name=None)]
    canonical.insert(0, "condition_id", keys)
    assert len(keys) == len(set(keys)), "condition ID collision or duplicate condition"
    canonical.to_csv(ROOT / "buchwald_hartwig_canonical.csv", index=False)
    pd.DataFrame(missing, columns=FACTORS).to_csv(ROOT / "unobserved_grid_conditions.csv", index=False)
    (ROOT / "workbook_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {k: v for k, v in report.items() if k not in ("factor_values", "sheets")}
    summary["sheet_count"] = len(sheets)
    summary["all_sheets_same_multiset"] = all(r["same_row_multiset_as_canonical"] for r in report["sheets"].values())
    summary["canonical_sheet_audit"] = report["sheets"]["FullCV_01"]
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
