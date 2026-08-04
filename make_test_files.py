#!/usr/bin/env python3
"""
Build synthetic old/new forecast files that mirror the REAL UKI/UKIMEA layouts
(real column names, real header row positions, dashboard junk above the header)
but with invented deal data plus a known ground truth, so the matcher can be
scored objectively instead of eyeballed.

Deliberately includes the awkward cases:
  * header row 10 (old) / row 7 (new), with a dashboard block above
  * different column sets, names and ORDER between the two files
  * decoy columns: 'PN Specialist', 'Manager (Formula)', 'Override Manager'
  * accounts with several concurrent opportunities (the real trap)
  * account renames, legal-suffix churn, punctuation and accent drift
  * opportunity names carrying fiscal-year/quarter noise that must be ignored
  * genuinely new deals, and old deals that dropped off
  * a TOTAL row at the bottom, and a blank spacer row
"""

import json
import random

import pandas as pd

random.seed(20260804)

OLD_HEADER_ROW = 10   # 1-based, as Excel shows it
NEW_HEADER_ROW = 7

MANAGERS = ["Sarah Whitfield", "Tom Okafor", "Priya Raman", "Marc Dubois"]
SPECIALISTS = ["James Lin", "Aoife Byrne", "Karl Jensen", "Nadia Haddad"]

# (old account, new account, old opp, new opp, old value, new value, should_match)
PAIRS = [
    # --- straightforward renewals, light name drift ---
    ("Barclays Bank PLC", "Barclays Bank Plc",
     "FY24 Q3 Storage Support Renewal", "FY25 Q3 Storage Support Renewal",
     412_000, 438_000, True),
    ("Deutsche Telekom AG", "Deutsche Telekom",
     "FY24 Compute Care Pack", "FY25 Compute Care Pack",
     870_500, 905_000, True),
    ("Société Générale S.A.", "Societe Generale SA",
     "FY24 Q2 Networking Support", "FY25 Q2 Networking Support",
     233_000, 241_500, True),
    ("Unilever N.V.", "Unilever NV",
     "FY24 Datacentre Care Renewal", "FY25 Datacentre Care Renewal",
     158_200, 149_000, True),

    # --- SAME ACCOUNT, MULTIPLE DEALS: account-name-only matching fails here ---
    ("Siemens AG", "Siemens AG",
     "FY24 Storage Support Renewal", "FY25 Storage Support Renewal",
     640_000, 672_000, True),
    ("Siemens AG", "Siemens AG",
     "FY24 Networking Care Pack", "FY25 Networking Care Pack",
     215_000, 228_000, True),
    ("Siemens AG", "Siemens AG",
     "FY24 Proactive Care Compute", "FY25 Proactive Care Compute",
     93_000, 101_000, True),
    ("Nestle S.A.", "Nestlé SA",
     "FY24 Q1 Server Support", "FY25 Q1 Server Support",
     305_000, 318_000, True),
    ("Nestle S.A.", "Nestlé SA",
     "FY24 Q1 Storage Expansion", "FY25 Q1 Storage Expansion",
     127_500, 133_000, True),

    # --- account renamed / restructured, deal is the same ---
    ("Royal Bank of Scotland Group", "NatWest Group Royal Bank of Scotland",
     "FY24 Mission Critical Support", "FY25 Mission Critical Support",
     521_000, 540_000, True),

    # --- big value swing, still a real renewal (flag, don't exclude) ---
    ("Vodafone Group Plc", "Vodafone Group",
     "FY24 Q4 Network Support Renewal", "FY25 Q4 Network Support Renewal",
     980_000, 340_000, True),

    # --- word order differs ---
    ("Bank of Ireland", "Ireland Bank of (BOI)",
     "FY24 Storage Care Renewal", "FY25 Storage Care Renewal",
     176_000, 182_000, True),

    # --- extra descriptive words on one side only ---
    ("Airbus", "Airbus Defence and Space Ltd",
     "FY24 HPC Support Contract", "FY25 HPC Support Contract",
     745_000, 760_000, True),
]

DROPPED = [   # only in the OLD file -> should be reported as dropped off
    ("Carrefour SA", "FY24 Retail Edge Support", 88_000),
    ("Telefonica S.A.", "FY24 Q2 Compute Renewal", 264_000),
    ("Heineken N.V.", "FY24 Storage Support", 119_500),
]

BRAND_NEW = [  # only in the NEW file -> should be reported as genuinely new
    ("Zalando SE", "FY25 GreenLake Private Cloud", 430_000),
    ("Ferrovial S.A.", "FY25 Q1 Edge Compute Services", 97_000),
    ("Maersk A/S", "FY25 Container Platform Support", 288_000),
]


def split_value(total):
    install = round(total * random.uniform(0.55, 0.85), 2)
    return install, round(total - install, 2)


def blank_row(headers):
    return {h: "" for h in headers}


def build():
    headers = json.load(open("real_headers.json"))
    old_h, new_h = headers["old"], headers["new"]
    old_rows, new_rows, truth = [], [], []

    def make_old(opp_id, acct, opp, value, mgr, spec, category):
        row = blank_row(old_h)
        ib, ex = split_value(value)
        row.update({
            "HPE Opportunity Id": opp_id, "Region": "UKI", "Country": "UK",
            "Account Name": acct, "Opportunity Name": opp,
            "Primary Pipeline Owner": mgr,
            "PN Specialist": "N/A",          # decoy column
            "IB Specialist": spec, "Manager": mgr,
            "Forecast Category": category, "Close Date": "2025-10-31",
            "Month": "Oct", "Install Base Total": ib, "Expand Total": ex,
            "IB & NS Total": value, "Total Change": 0,
        })
        return row

    def make_new(opp_id, acct, opp, value, mgr, spec, category):
        row = blank_row(new_h)
        ib, ex = split_value(value)
        row.update({
            "HPE Opportunity ID": opp_id, "Country": "UK", "Sub GEO": "UKI",
            "Account Name": acct, "Opportunity Name": opp,
            "Primary Pipeline Owner": mgr, "Aligned IB Specialist": spec,
            "Manager (Formula)": "ERROR",     # decoy column
            "Override Manager": "",           # decoy column
            "Manager": mgr,
            "Forecast Category": category, "RTM": "Direct", "WK": 32,
            "Close Date": "2026-01-31", "Month": "Jan",
            "Install Base Total": ib, "Expand Total": ex,
            "IB & NS Total": value, "Total Change": 0,
        })
        return row

    for idx, (o_acct, n_acct, o_opp, n_opp, o_val, n_val, ok) in enumerate(PAIRS):
        mgr, spec = MANAGERS[idx % 4], SPECIALISTS[idx % 4]
        old_id, new_id = f"OPP-8{idx:04d}", f"OPP-9{idx:04d}"
        old_rows.append(make_old(old_id, o_acct, o_opp, o_val, mgr, spec, "Commit"))
        new_rows.append(make_new(new_id, n_acct, n_opp, n_val, mgr, spec, "Commit"))
        truth.append((new_id, old_id if ok else None))

    for idx, (acct, opp, val) in enumerate(DROPPED):
        old_rows.append(make_old(f"OPP-7{idx:04d}", acct, opp, val,
                                 MANAGERS[idx % 4], SPECIALISTS[idx % 4], "Best Case"))

    for idx, (acct, opp, val) in enumerate(BRAND_NEW):
        new_id = f"OPP-6{idx:04d}"
        new_rows.append(make_new(new_id, acct, opp, val,
                                 MANAGERS[idx % 4], SPECIALISTS[idx % 4], "Pipeline"))
        truth.append((new_id, None))

    old_df = pd.DataFrame(old_rows, columns=old_h)
    new_df = pd.DataFrame(new_rows, columns=new_h)

    # Blank spacer + TOTAL row, as the real exports carry.
    for frame in (old_df, new_df):
        frame.loc[len(frame)] = blank_row(list(frame.columns))
        total = blank_row(list(frame.columns))
        total["Account Name"] = "TOTAL"
        total["IB & NS Total"] = pd.to_numeric(
            frame["IB & NS Total"], errors="coerce").sum()
        frame.loc[len(frame)] = total

    def write(path, frame, header_row, dashboard):
        """Write with a dashboard block above, so the header lands on header_row."""
        sheet = "Current Wk Forecast File"
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            frame.to_excel(writer, sheet_name=sheet, index=False,
                           startrow=header_row - 1)
            ws = writer.sheets[sheet]
            for r, c, text in dashboard:
                ws.write(r, c, text)

    write("test_old.xlsx", old_df, OLD_HEADER_ROW, [
        (0, 0, "CSLV Forecast File"), (0, 5, "UKI OS Forecast"),
        (0, 6, "Key Deals in Forecast"), (0, 9, "Most Likely Forecast"),
        (1, 5, "Install Base"), (2, 5, "UK Install Base"),
        (4, 5, "Expand"), (5, 5, "UK New Solution"),
    ])
    write("test_new.xlsx", new_df, NEW_HEADER_ROW, [
        (0, 0, "UKIMEA CSLV Forecast File"), (0, 8, "Errors"), (0, 11, "#"),
        (1, 8, "UKI"), (2, 8, "ME"), (3, 8, "EA"),
        (5, 6, "Red = Over 14 days since update"), (5, 18, "Red = Overdue"),
    ])

    pd.DataFrame(truth, columns=["new_id", "expected_old_id"]).to_csv(
        "test_truth.csv", index=False)

    print(f"test_old.xlsx  : {len(old_df)} rows, {len(old_h)} cols, "
          f"header on row {OLD_HEADER_ROW}")
    print(f"test_new.xlsx  : {len(new_df)} rows, {len(new_h)} cols, "
          f"header on row {NEW_HEADER_ROW}")
    print(f"test_truth.csv : {len(truth)} rows "
          f"({sum(1 for _, o in truth if o)} real renewals, "
          f"{sum(1 for _, o in truth if not o)} new deals)")
    print(f"Expected dropped off: {len(DROPPED)}")


if __name__ == "__main__":
    build()
