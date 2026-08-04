#!/usr/bin/env python3
"""Score the matcher's output against the known ground truth."""

import sys

import pandas as pd

results = pd.read_excel("renewal_matches.xlsx", sheet_name="All New Rows + Match")
truth = pd.read_csv("test_truth.csv")

got = {
    str(r["HPE Opportunity ID"]): (
        str(r["Matched Opportunity ID"]) if pd.notna(r["Matched Opportunity ID"])
        and str(r["Matched Opportunity ID"]).strip() else None
    )
    for _, r in results.iterrows()
}
score = {
    str(r["HPE Opportunity ID"]): r["Match Score %"] for _, r in results.iterrows()
}
status = {
    str(r["HPE Opportunity ID"]): r["Match Status"] for _, r in results.iterrows()
}

correct = wrong = missed = false_pos = 0
print(f"{'New ID':<10} {'Expected':<10} {'Got':<10} {'Score':>7}  {'Status':<16} Verdict")
print("-" * 82)

for _, row in truth.iterrows():
    new_id = str(row["new_id"])
    expected = row["expected_old_id"]
    expected = None if pd.isna(expected) else str(expected)
    actual = got.get(new_id)

    if expected == actual:
        verdict, _ = "CORRECT", correct
        correct += 1
    elif expected is None and actual is not None:
        verdict = "FALSE POSITIVE"
        false_pos += 1
    elif expected is not None and actual is None:
        verdict = "MISSED"
        missed += 1
    else:
        verdict = f"WRONG (wanted {expected})"
        wrong += 1

    print(f"{new_id:<10} {str(expected or '-'):<10} {str(actual or '-'):<10} "
          f"{score.get(new_id, 0):>7.1f}  {str(status.get(new_id, '')):<16} {verdict}")

total = len(truth)
print("-" * 82)
print(f"Correct        : {correct}/{total}")
print(f"Wrong pairing  : {wrong}")
print(f"Missed renewal : {missed}")
print(f"False positive : {false_pos}")

dropped = pd.read_excel("renewal_matches.xlsx", sheet_name="Dropped Off")
dropped_names = sorted(dropped["Account Name"].dropna().astype(str).tolist())
expected_dropped = sorted(["Carrefour SA", "Telefonica S.A.", "Heineken N.V."])
print(f"\nDropped off detected : {dropped_names}")
print(f"Dropped off expected : {expected_dropped}")
drop_ok = dropped_names == expected_dropped
print(f"Dropped-off check    : {'PASS' if drop_ok else 'FAIL'}")

ok = correct == total and drop_ok
print(f"\n{'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}")
sys.exit(0 if ok else 1)
