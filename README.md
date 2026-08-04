# HPE Forecast Renewal Matcher

Matches deals in a **new** forecast export back to deals in an **old** export,
where the HPE Opportunity ID has been reissued and the Account / Opportunity
names have drifted. Answers: what carried over, what is genuinely new, and what
dropped off.

## Why Python rather than the VBA macro

The VBA works, but three things are hard to fix inside Excel:

| | VBA macro | This tool |
|---|---|---|
| 434 x 434 rows | ~5-10 min (est.) | **0.18 s** (measured) |
| 1500 x 1500 rows | ~1-2 hrs (est.) | **1.21 s** (measured) |
| Column references | Hardcoded letters | Found by header name |
| Verification | Run blind, eyeball it | Scored against ground truth |

The VBA timings are estimates: a faithful Python port of that exact algorithm
measured 111 microseconds per pair (21 s for 434x434), and VBA adds a
`WorksheetFunction.Min` COM round-trip on **every character comparison** on top
of that, which is what makes it slow. This tool uses `rapidfuzz`, whose matrix
comparison is vectorised C++.

## Install

```bash
pip install pandas openpyxl rapidfuzz xlsxwriter numpy
```

## Use

```bash
# 1. Confirm it reads your files correctly (does not match, does not write)
python3 renewal_match.py --old OLD.xlsx --new NEW.xlsx --inspect

# 2. Run the match
python3 renewal_match.py --old OLD.xlsx --new NEW.xlsx --out results.xlsx
```

Options: `--old-sheet` / `--new-sheet` to override tab detection,
`--confident-at` / `--floor` to move the confidence bands.

**Source files are never modified.** Results go to a new workbook, so nothing
can land on top of real forecast columns.

## Confirmed against the real files

Both uploads were opened and verified column-by-column. The structure differs
from the screenshot in ways that matter:

| | Old (`UKI_OS_Q1_Forecast_21.01.26_consolidated`) | New (`UKIMEA_OS_Q1_Forecast`) |
|---|---|---|
| Sheet | `Current Wk Forecast File` | `Current Wk Forecast File` |
| Header row | **10** (dashboard above) | **7** (dashboard above) |
| Columns | 59 (A:BG) | 55 (A:BC) |
| Account Name | E | E |
| Opportunity Name | F | F |
| Manager | K | **L** |
| IB Specialist | J (`IB Specialist`) | I (`Aligned IB Specialist`) |
| **IB & NS Total** | **AI** | **AG** |
| Opportunity ID | A (`HPE Opportunity Id`) | A (`HPE Opportunity ID`) |

Both files also carry decoy columns the matcher has to avoid: the old file has
`PN Specialist` next to `IB Specialist`; the new file has `Manager (Formula)`
and `Override Manager` next to `Manager`. Column detection picks the right one
in each case.

Hidden sheets in the new file (`Look Up Tables`, `Summaries for Consolidation`)
are ignored.

### The VBA column letters were wrong on both files

The macro read account names from column **B** — that is `Region` (old) and
`Country` (new). It read values from column **K** — that is `Manager` (old) and
`Override Manager` (new), so the value subtraction was operating on names. And
it wrote output to **N:Q**, which holds real data in both files:

- Old N:Q = `IB Value`, `New Sol Value`, `Clari Call`, `Primary Reseller`
- New N:Q = `Deal Based Call`, `Primary Reseller`, `Primary Distributor`, `RTM`

## How matching works

1. **Normalise** both names: strip accents, punctuation, legal suffixes
   (Ltd/PLC/GmbH/S.A./N.V. ...), and single-letter fragments. Opportunity names
   additionally have FY/quarter/week/year/long-digit noise removed, since those
   change between exports *by design*.
2. **Score** account and opportunity names with `token_set_ratio`, which is
   robust to word reordering and to one side carrying extra words.
3. **Blend** 60% account + 40% opportunity, then add +5 for same Manager and +5
   for same IB Specialist.
4. **Gate**: account similarity below 70 is never a candidate — a different
   customer is not a renewal however well the opportunity names read. The rep
   bonus cannot rescue a pair that fails on names alone.
5. **Assign one-to-one**, best pairs first. A renewal is one old deal becoming
   one new deal, so an old row is never claimed twice.

### Why not account name alone

One account routinely has several live opportunities. Matching on account name
alone gives all of them an identical score, so the tie is broken arbitrarily.
The test set includes Siemens AG with three concurrent deals and Nestlé with
two; the opportunity-name component is what separates them.

### Bands

- **>= 85** confident match
- **50-84** needs review
- **< 50** no match (new deal, or dropped off)

Value change is reported and flagged at +/-50%, but **never excludes a match** —
per the brief, a big swing is a review flag, not a disqualifier.

## Output workbook

| Sheet | Contents |
|---|---|
| `Summary` | Counts and value roll-up: carried over, new, dropped off |
| `All New Rows + Match` | Every new-file column, plus 13 match columns appended at the far right |
| `Confident` | Score >= 85 |
| `Needs Review` | Score 50-84, plus anything flagged |
| `New Deals` | No match found |
| `Dropped Off` | Old rows nothing matched to |

## Verification

Both uploads are blanked (0 data rows), so the matcher could not be scored on
real deals. Instead `make_test_files.py` builds fixtures that **replicate the
real layouts exactly** — same sheet name, same 59/55 column headers, same header
rows 10 and 7, same dashboard blocks above, same decoy columns — populated with
invented deals whose correct answers are known.

```bash
python3 make_test_files.py
python3 renewal_match.py --old test_old.xlsx --new test_new.xlsx --out renewal_matches.xlsx
python3 verify.py
```

Current result: **16/16 correct, 0 wrong pairings, 0 missed renewals,
0 false positives**, dropped-off detection exact.

The fixtures deliberately include the cases that break naive matching:
accents (`Nestle S.A.` / `Nestlé SA`), legal-suffix churn, one account with
three concurrent deals, an account rename (`Royal Bank of Scotland Group` /
`NatWest Group Royal Bank of Scotland`), reordered words (`Bank of Ireland` /
`Ireland Bank of (BOI)`), extra words on one side (`Airbus` / `Airbus Defence
and Space Ltd`), and a genuine renewal whose value fell 65% (Vodafone) which
must still match but be flagged.

Two bugs were found and fixed this way, both of which would have shipped silently:
`Ferrovial S.A.` matching `Telefonica S.A.` on shared `s`/`a` fragments, and
European-format numbers (`1.234,50`) parsing as `1.2345`.

## Before trusting a real run

1. Run `--inspect` first and check every resolved column.
2. Work the `Needs Review` tab — that band exists to be read by a human.
3. Spot-check ~10 `Confident` rows.
4. Sanity-check `Dropped Off` against what you know actually lapsed.

Account names in your real data will be messier than the fixtures. If genuine
renewals are landing in `New Deals`, lower `ACCOUNT_GATE` (top of the script);
if unrelated deals are pairing up, raise it.
