#!/usr/bin/env python3
"""
HPE Forecast Renewal Matcher
============================

Matches deals in a NEW forecast export back to deals in an OLD forecast export,
where the HPE Opportunity ID has changed (renewals get reissued IDs) and the
Account / Opportunity names may differ slightly.

Usage:
    python3 renewal_match.py --old OLD.xlsx --new NEW.xlsx --out results.xlsx

    # if sheet auto-detection picks the wrong tab:
    python3 renewal_match.py --old OLD.xlsx --new NEW.xlsx \
        --old-sheet "Nov Forecast" --new-sheet "Aug Forecast" --out results.xlsx

    # just look at the files without matching:
    python3 renewal_match.py --old OLD.xlsx --new NEW.xlsx --inspect

Nothing is ever written back into the source files. Results go to a brand new
workbook, so there is no risk of landing on top of real forecast columns.
"""

import argparse
import re
import sys
import unicodedata

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

# --------------------------------------------------------------------------
# Tunables
# --------------------------------------------------------------------------

W_ACCOUNT = 0.60          # weight of account-name similarity in the blended score
W_OPPORTUNITY = 0.40      # weight of opportunity-name similarity
BONUS_MANAGER = 5.0       # added if the same Manager owns both rows
BONUS_SPECIALIST = 5.0    # added if the same IB Specialist owns both rows

ACCOUNT_GATE = 70.0       # below this account similarity, never a candidate
ASSIGN_FLOOR = 50.0       # below this blended score, treat as "no match"
CONFIDENT_AT = 85.0       # at/above this blended score, treat as confident

BIG_SWING_PCT = 50.0      # flag matched pairs whose value moved more than this


# --------------------------------------------------------------------------
# Text normalisation
# --------------------------------------------------------------------------

# Corporate/legal suffixes that add noise without adding identity.
LEGAL_TOKENS = {
    "ltd", "limited", "plc", "inc", "incorporated", "llc", "llp", "lp",
    "gmbh", "mbh", "ag", "kg", "kgaa", "sa", "sas", "sarl", "sl", "spa",
    "srl", "nv", "bv", "cv", "oy", "oyj", "ab", "as", "asa", "aps", "kft",
    "zrt", "doo", "dd", "pty", "pte", "sdn", "bhd", "co", "corp",
    "corporation", "company", "holding", "holdings", "group", "grp",
    "international", "intl", "worldwide", "global", "europe", "emea",
    "the", "and", "of",
}

# Tokens that legitimately change between an old and new forecast export and
# therefore must not drive (or block) a match: fiscal years, quarters, weeks,
# bare years, and long digit runs such as contract or quote numbers.
NOISE_PATTERNS = [
    re.compile(r"\bfy\s*\d{2,4}\b"),
    re.compile(r"\bq[1-4]\b"),
    re.compile(r"\bwk\s*\d{1,2}\b"),
    re.compile(r"\b(?:19|20)\d{2}\b"),
    re.compile(r"\b\d{5,}\b"),
]


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _tokenise(text: str) -> list[str]:
    """
    Lower, de-accent, and split into identifying tokens.

    Periods are deleted rather than turned into spaces, so "S.A." collapses to
    the single token "sa" and is recognised as a legal suffix. Leaving it as
    "s a" would otherwise let two unrelated companies share two tokens and
    score far higher than they deserve.
    """
    text = _strip_accents(text).lower()
    text = text.replace(".", "")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [
        t for t in text.split()
        if len(t) > 1 and t not in LEGAL_TOKENS
    ]


def normalise_account(value) -> str:
    """Normalise an account name down to its identifying words."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return " ".join(_tokenise(str(value)))


def normalise_opportunity(value) -> str:
    """Normalise an opportunity name, dropping date/quarter/ID noise."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = _strip_accents(str(value)).lower()
    for pattern in NOISE_PATTERNS:
        text = pattern.sub(" ", text)
    return " ".join(_tokenise(text))


def normalise_person(value) -> str:
    """Normalise a person's name for equality comparison only."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = _strip_accents(str(value)).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(sorted(text.split()))


def to_number(value) -> float:
    """Coerce a currency-ish cell to a float. Returns NaN when not numeric."""
    if value is None:
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return np.nan if pd.isna(value) else float(value)
    text = str(value).strip()
    if not text:
        return np.nan
    negative = text.startswith("(") and text.endswith(")")

    # Decide which separator is the decimal point before stripping anything.
    # UKIMEA covers countries that export "1.234,50" as well as "1,234.50";
    # when both appear, the rightmost one is the decimal separator.
    has_dot, has_comma = "." in text, "," in text
    if has_dot and has_comma:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma:
        # A lone comma is a decimal point only in "123,4" / "123,45" form;
        # anything else (1,234 / 1,234,567) is a thousands separator.
        text = (
            text.replace(",", ".")
            if re.search(r",\d{1,2}$", text) and text.count(",") == 1
            else text.replace(",", "")
        )

    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", "-", ".", "-."}:
        return np.nan
    try:
        number = float(text)
    except ValueError:
        return np.nan
    return -number if negative else number


# --------------------------------------------------------------------------
# Reading the workbooks
# --------------------------------------------------------------------------

# Logical field -> regexes tried in order against the real header text.
COLUMN_PATTERNS = {
    "opp_id": [r"opportunity\s*id", r"\bopp\w*\s*id\b", r"\bid\b"],
    "account": [r"account\s*name", r"\baccount\b", r"customer"],
    "opportunity": [r"opportunity\s*name", r"\bopportunity\b(?!\s*(id|updates))"],
    "manager": [r"^manager$", r"\bmanager\b(?!/)"],
    "specialist": [r"aligned\s*ib\s*specialist", r"ib\s*specialist", r"specialist"],
    "value": [r"ib\s*&\s*ns\s*total", r"ib\s*and\s*ns\s*total", r"ib.{0,5}ns.{0,5}total"],
    "install_base": [r"install\s*base\s*total"],
    "expand": [r"expand\s*total"],
    "close_date": [r"close\s*date"],
    "forecast_category": [r"forecast\s*category"],
    "country": [r"^country$", r"\bcountry\b"],
    "owner": [r"primary\s*pipeline\s*owner", r"pipeline\s*owner", r"\bowner\b"],
}

HEADER_HINTS = [
    "opportunity", "account", "manager", "forecast", "close", "total",
    "specialist", "owner", "country", "month",
]


def _header_score(row) -> int:
    """How much does this row look like a header row?"""
    cells = [str(c).strip().lower() for c in row if pd.notna(c) and str(c).strip()]
    if len(cells) < 4:
        return 0
    return sum(1 for cell in cells for hint in HEADER_HINTS if hint in cell)


def load_sheet(path: str, sheet: str | None, max_header_scan: int = 20):
    """
    Read a sheet, auto-detecting both the tab and the header row.

    Returns (dataframe, sheet_name, header_row_index_zero_based).
    """
    if path.lower().endswith((".csv", ".tsv")):
        sep = "\t" if path.lower().endswith(".tsv") else ","
        raw = pd.read_csv(path, sep=sep, header=None, dtype=object)
        header_idx = max(
            range(min(max_header_scan, len(raw))),
            key=lambda i: _header_score(raw.iloc[i]),
        )
        frame = pd.read_csv(path, sep=sep, header=header_idx, dtype=object)
        return frame, "(csv)", header_idx

    book = pd.ExcelFile(path)
    candidates = [sheet] if sheet else book.sheet_names
    if sheet and sheet not in book.sheet_names:
        raise SystemExit(
            f"Sheet {sheet!r} not found in {path}. Available: {book.sheet_names}"
        )

    best = None  # (score, sheet_name, header_idx)
    for name in candidates:
        raw = book.parse(name, header=None, dtype=object, nrows=max_header_scan)
        if raw.empty:
            continue
        for i in range(len(raw)):
            score = _header_score(raw.iloc[i])
            if best is None or score > best[0]:
                best = (score, name, i)

    if best is None or best[0] == 0:
        raise SystemExit(
            f"Could not find a header row in {path}. "
            f"Pass the tab explicitly with --old-sheet / --new-sheet."
        )

    _, sheet_name, header_idx = best
    frame = book.parse(sheet_name, header=header_idx, dtype=object)
    frame = frame.loc[:, [c for c in frame.columns if not str(c).startswith("Unnamed")]]
    return frame, sheet_name, header_idx


def resolve_columns(frame: pd.DataFrame) -> dict:
    """Map logical field names onto the real column labels in this frame."""
    headers = {str(c): str(c).strip().lower() for c in frame.columns}
    resolved = {}
    taken = set()
    for field, patterns in COLUMN_PATTERNS.items():
        for pattern in patterns:
            hit = next(
                (
                    original
                    for original, lowered in headers.items()
                    if original not in taken and re.search(pattern, lowered)
                ),
                None,
            )
            if hit:
                resolved[field] = hit
                taken.add(hit)
                break
    return resolved


def describe(label: str, path: str, frame, sheet, header_idx, columns) -> None:
    print(f"\n{'=' * 70}\n{label}: {path}\n{'=' * 70}")
    print(f"  Sheet          : {sheet}")
    print(f"  Header row     : {header_idx + 1} (1-based, as Excel shows it)")
    print(f"  Data rows      : {len(frame)}")
    print(f"  Columns ({len(frame.columns)}):")
    for i, col in enumerate(frame.columns):
        letter = chr(ord("A") + i) if i < 26 else f"A{chr(ord('A') + i - 26)}"
        print(f"      {letter:>3}  {col}")
    print("  Resolved for matching:")
    for field in COLUMN_PATTERNS:
        found = columns.get(field)
        mark = "OK " if found else "-- "
        print(f"      {mark} {field:<18} -> {found or '(not found)'}")


# --------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------

def build_frame(frame: pd.DataFrame, columns: dict) -> pd.DataFrame:
    """Pull out the fields we match on, keeping the original row number."""
    out = pd.DataFrame(index=frame.index)
    out["account_raw"] = frame[columns["account"]] if "account" in columns else ""
    out["opp_raw"] = frame[columns["opportunity"]] if "opportunity" in columns else ""
    out["opp_id"] = frame[columns["opp_id"]] if "opp_id" in columns else ""
    out["manager"] = frame[columns["manager"]] if "manager" in columns else ""
    out["specialist"] = frame[columns["specialist"]] if "specialist" in columns else ""
    out["value"] = (
        frame[columns["value"]].map(to_number) if "value" in columns else np.nan
    )

    out["account_key"] = out["account_raw"].map(normalise_account)
    out["opp_key"] = out["opp_raw"].map(normalise_opportunity)
    out["manager_key"] = out["manager"].map(normalise_person)
    out["specialist_key"] = out["specialist"].map(normalise_person)

    # Drop blank rows and spreadsheet total/subtotal lines.
    blank = out["account_key"].str.strip() == ""
    totals = out["account_raw"].astype(str).str.strip().str.lower().isin(
        {"total", "totals", "grand total", "subtotal", "sum"}
    )
    return out[~(blank | totals)].copy()


def score_matrix(new_df: pd.DataFrame, old_df: pd.DataFrame) -> np.ndarray:
    """
    Blended similarity for every (new, old) pair.

    token_set_ratio is used rather than raw Levenshtein because it is robust to
    word reordering and to one name carrying extra words the other does not --
    both common between forecast exports.
    """
    account = process.cdist(
        new_df["account_key"], old_df["account_key"],
        scorer=fuzz.token_set_ratio, dtype=np.float32, workers=-1,
    )
    opportunity = process.cdist(
        new_df["opp_key"], old_df["opp_key"],
        scorer=fuzz.token_set_ratio, dtype=np.float32, workers=-1,
    )

    base = W_ACCOUNT * account + W_OPPORTUNITY * opportunity
    blended = base.copy()

    # Same rep on both sides raises confidence; blanks never earn a bonus.
    for field, bonus in (("manager_key", BONUS_MANAGER),
                         ("specialist_key", BONUS_SPECIALIST)):
        new_vals = new_df[field].to_numpy()
        old_vals = old_df[field].to_numpy()
        same = (new_vals[:, None] == old_vals[None, :])
        same &= (new_vals != "")[:, None]
        blended += np.where(same, bonus, 0.0).astype(np.float32)

    blended = np.clip(blended, 0, 100)

    # A different customer is never a renewal, however well the opp names read.
    blended[account < ACCOUNT_GATE] = 0.0

    # The rep bonus is a confidence signal, not a rescue: a pair that fails on
    # names alone must not be dragged over the line just because one manager
    # happens to own both rows.
    blended[base < ASSIGN_FLOOR] = 0.0
    return blended, account, opportunity


def assign(blended: np.ndarray) -> dict:
    """
    One-to-one assignment, best pairs first.

    A renewal is one old deal becoming one new deal, so an old row must not be
    claimed twice. Walking candidate pairs in descending score order and taking
    each only if both sides are still free gives a stable, explainable result.
    """
    n_new, n_old = blended.shape
    if n_new == 0 or n_old == 0:
        return {}

    flat = blended.ravel()
    eligible = np.flatnonzero(flat >= ASSIGN_FLOOR)
    order = eligible[np.argsort(-flat[eligible], kind="stable")]

    pairs = {}
    used_old = set()
    for idx in order:
        i, j = divmod(int(idx), n_old)
        if i in pairs or j in used_old:
            continue
        pairs[i] = j
        used_old.add(j)
        if len(pairs) == min(n_new, n_old):
            break
    return pairs


def band(score: float) -> str:
    if score >= CONFIDENT_AT:
        return "Confident match"
    if score >= ASSIGN_FLOOR:
        return "Needs review"
    return "No match"


def match(new_df: pd.DataFrame, old_df: pd.DataFrame) -> pd.DataFrame:
    blended, account, opportunity = score_matrix(new_df, old_df)
    pairs = assign(blended)

    new_pos = {label: i for i, label in enumerate(new_df.index)}
    old_labels = list(old_df.index)

    rows = []
    for label in new_df.index:
        i = new_pos[label]
        new_row = new_df.loc[label]
        j = pairs.get(i)

        record = {
            "_new_label": label,
            "New Account Name": new_row["account_raw"],
            "New Opportunity Name": new_row["opp_raw"],
            "New Opportunity ID": new_row["opp_id"],
            "New IB & NS Total": new_row["value"],
        }

        if j is None:
            best_j = int(np.argmax(blended[i])) if blended.shape[1] else None
            near = (
                float(blended[i, best_j]) if best_j is not None else 0.0
            )
            record.update({
                "_old_label": None,
                "Match Status": "No match",
                "Matched Account Name": "",
                "Matched Opportunity Name": "",
                "Matched Opportunity ID": "",
                "Match Score %": 0.0,
                "Account Similarity %": 0.0,
                "Opportunity Similarity %": 0.0,
                "Same Manager": "",
                "Same IB Specialist": "",
                "Old IB & NS Total": np.nan,
                "Value Difference": np.nan,
                "Value Change %": np.nan,
                "Review Flag": (
                    "New deal - no candidate above threshold"
                    f" (closest scored {near:.1f}%)"
                ),
            })
            rows.append(record)
            continue

        old_label = old_labels[j]
        old_row = old_df.loc[old_label]
        score = float(blended[i, j])
        new_value = new_row["value"]
        old_value = old_row["value"]
        diff = (
            new_value - old_value
            if pd.notna(new_value) and pd.notna(old_value)
            else np.nan
        )
        pct = (
            (diff / old_value * 100.0)
            if pd.notna(diff) and pd.notna(old_value) and old_value != 0
            else np.nan
        )

        same_mgr = (
            new_row["manager_key"] != ""
            and new_row["manager_key"] == old_row["manager_key"]
        )
        same_spec = (
            new_row["specialist_key"] != ""
            and new_row["specialist_key"] == old_row["specialist_key"]
        )

        flags = []
        if score < CONFIDENT_AT:
            flags.append("Score in review band")
        if pd.notna(pct) and abs(pct) >= BIG_SWING_PCT:
            flags.append(f"Value moved {pct:+.0f}%")
        if pd.isna(new_value) or pd.isna(old_value):
            flags.append("Missing value on one side")
        if not same_mgr and not same_spec:
            flags.append("Different Manager and IB Specialist")

        record.update({
            "_old_label": old_label,
            "Match Status": band(score),
            "Matched Account Name": old_row["account_raw"],
            "Matched Opportunity Name": old_row["opp_raw"],
            "Matched Opportunity ID": old_row["opp_id"],
            "Match Score %": round(score, 1),
            "Account Similarity %": round(float(account[i, j]), 1),
            "Opportunity Similarity %": round(float(opportunity[i, j]), 1),
            "Same Manager": "Yes" if same_mgr else "No",
            "Same IB Specialist": "Yes" if same_spec else "No",
            "Old IB & NS Total": old_value,
            "Value Difference": diff,
            "Value Change %": round(pct, 1) if pd.notna(pct) else np.nan,
            "Review Flag": "; ".join(flags),
        })
        rows.append(record)

    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

RESULT_COLUMNS = [
    "Match Status", "Match Score %", "Account Similarity %",
    "Opportunity Similarity %", "Matched Opportunity ID", "Matched Account Name",
    "Matched Opportunity Name", "Same Manager", "Same IB Specialist",
    "Old IB & NS Total", "Value Difference", "Value Change %", "Review Flag",
]


def write_output(path, results, new_raw, old_raw, old_df, new_cols, old_cols):
    """Write a fresh results workbook. Source files are never touched."""
    matched_old = {
        lbl for lbl in results["_old_label"].dropna().tolist()
    }
    dropped = old_df.index.difference(pd.Index(list(matched_old)))

    # Full new-file data with the match columns appended on the right.
    enriched = new_raw.loc[results["_new_label"]].reset_index(drop=True)
    for col in RESULT_COLUMNS:
        enriched[col] = results[col].to_numpy()

    confident = results[results["Match Status"] == "Confident match"]
    review = results[results["Match Status"] == "Needs review"]
    unmatched = results[results["Match Status"] == "No match"]

    dropped_rows = old_raw.loc[dropped].copy() if len(dropped) else old_raw.iloc[0:0].copy()

    def money(series):
        vals = pd.to_numeric(series, errors="coerce")
        return float(vals.sum(skipna=True)) if len(vals) else 0.0

    summary = pd.DataFrame([
        ("Rows in new file", len(results)),
        ("Rows in old file", len(old_df)),
        ("", ""),
        (f"Confident matches (>= {CONFIDENT_AT:.0f}%)", len(confident)),
        (f"Needs review ({ASSIGN_FLOOR:.0f}-{CONFIDENT_AT:.0f}%)", len(review)),
        (f"No match / new deals (< {ASSIGN_FLOOR:.0f}%)", len(unmatched)),
        ("Old rows that dropped off", len(dropped)),
        ("", ""),
        ("New file total IB & NS", money(results["New IB & NS Total"])),
        ("Carried-over value (matched, new)", money(
            results.loc[results["Match Status"] != "No match", "New IB & NS Total"])),
        ("Carried-over value (matched, old)", money(
            results.loc[results["Match Status"] != "No match", "Old IB & NS Total"])),
        ("Net value change on matched deals", money(results["Value Difference"])),
        ("Value of genuinely new deals", money(unmatched["New IB & NS Total"])),
        ("", ""),
        ("Pairs flagged for a value swing", int(
            results["Review Flag"].str.contains("Value moved", na=False).sum())),
    ], columns=["Metric", "Value"])

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        enriched.to_excel(writer, sheet_name="All New Rows + Match", index=False)
        confident.drop(columns=["_new_label", "_old_label"]).to_excel(
            writer, sheet_name="Confident", index=False)
        review.drop(columns=["_new_label", "_old_label"]).to_excel(
            writer, sheet_name="Needs Review", index=False)
        unmatched.drop(columns=["_new_label", "_old_label"]).to_excel(
            writer, sheet_name="New Deals", index=False)
        dropped_rows.to_excel(writer, sheet_name="Dropped Off", index=False)

        book = writer.book
        header_fmt = book.add_format({
            "bold": True, "bg_color": "#01A982", "font_color": "white",
            "border": 1, "text_wrap": True, "valign": "vcenter",
        })
        for sheet_name, frame in (
            ("Summary", summary),
            ("All New Rows + Match", enriched),
            ("Confident", confident.drop(columns=["_new_label", "_old_label"])),
            ("Needs Review", review.drop(columns=["_new_label", "_old_label"])),
            ("New Deals", unmatched.drop(columns=["_new_label", "_old_label"])),
            ("Dropped Off", dropped_rows),
        ):
            sheet_obj = writer.sheets[sheet_name]
            for col_idx, col_name in enumerate(frame.columns):
                sheet_obj.write(0, col_idx, str(col_name), header_fmt)
                width = min(max(len(str(col_name)) + 2, 12), 42)
                sheet_obj.set_column(col_idx, col_idx, width)
            if len(frame):
                sheet_obj.freeze_panes(1, 0)
                sheet_obj.autofilter(0, 0, len(frame), max(len(frame.columns) - 1, 0))

    return summary, len(dropped)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main(argv=None):
    global CONFIDENT_AT, ASSIGN_FLOOR

    parser = argparse.ArgumentParser(description="Match HPE forecast renewals.")
    parser.add_argument("--old", required=True, help="Old forecast export")
    parser.add_argument("--new", required=True, help="New forecast export")
    parser.add_argument("--out", default="renewal_matches.xlsx", help="Output workbook")
    parser.add_argument("--old-sheet", default=None)
    parser.add_argument("--new-sheet", default=None)
    parser.add_argument("--inspect", action="store_true",
                        help="Show detected sheets/columns and exit")
    parser.add_argument("--confident-at", type=float, default=CONFIDENT_AT)
    parser.add_argument("--floor", type=float, default=ASSIGN_FLOOR)
    args = parser.parse_args(argv)

    CONFIDENT_AT = args.confident_at
    ASSIGN_FLOOR = args.floor

    old_raw, old_sheet, old_hdr = load_sheet(args.old, args.old_sheet)
    new_raw, new_sheet, new_hdr = load_sheet(args.new, args.new_sheet)
    old_cols = resolve_columns(old_raw)
    new_cols = resolve_columns(new_raw)

    describe("OLD FILE", args.old, old_raw, old_sheet, old_hdr, old_cols)
    describe("NEW FILE", args.new, new_raw, new_sheet, new_hdr, new_cols)

    missing = [
        (label, field)
        for label, cols in (("old", old_cols), ("new", new_cols))
        for field in ("account", "opportunity", "value")
        if field not in cols
    ]
    if missing:
        print("\nERROR: required columns not found:")
        for label, field in missing:
            print(f"  {label} file is missing a '{field}' column")
        print("Check the header row, or rename the column to match.")
        return 1

    if args.inspect:
        print("\n--inspect given, stopping before matching.")
        return 0

    old_df = build_frame(old_raw, old_cols)
    new_df = build_frame(new_raw, new_cols)
    print(f"\nMatching {len(new_df)} new rows against {len(old_df)} old rows "
          f"({len(new_df) * len(old_df):,} comparisons)...")

    results = match(new_df, old_df)
    summary, dropped_count = write_output(
        args.out, results, new_raw, old_raw, old_df, new_cols, old_cols
    )

    print(f"\n{'=' * 70}\nRESULTS\n{'=' * 70}")
    for _, row in summary.iterrows():
        if row["Metric"]:
            value = row["Value"]
            shown = f"{value:,.0f}" if isinstance(value, float) else value
            print(f"  {str(row['Metric']):<42} {shown}")
    print(f"\nWritten to: {args.out}")
    print("Source files were not modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
