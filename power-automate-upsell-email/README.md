# Untapped Services Upsell — Automated Email Flow (Power Automate)

Sends a personalised HPE eMemo-styled email to every rep in an Excel file, showing their
tracked (tapped) vs untracked (untapped) services value and their opportunity counts by
upsell reason.

**Files in this folder**

| File | Purpose |
|---|---|
| `HPE_Upsell_Merge_Template.html` | The HPE eMemo template with `{{placeholders}}` ready to paste into the Send email action |

**Source data columns (must match exactly):**
`Feedback Progress` · `Manager entitlement` · `Tracked Sum` · `Untracked Sum` · `CC / Day 1 Upsell Count` · `Low Pen Rate Count` · `No Services Op Count` · `Email`

---

## Part 0 — Prepare the Excel file (one-time)

1. Store the workbook in **OneDrive for Business** or a **SharePoint document library** (the Excel connector cannot read local files).
2. Open the workbook, select the data range **including the header row** → **Insert → Table** → tick *My table has headers*.
3. On the **Table Design** ribbon tab, rename the table to `UpsellData`.
4. Do not rename columns later — the flow references them by exact name and will break silently if they change.
5. Leave `Tracked Sum` / `Untracked Sum` as plain numbers (no currency symbols typed into cells). The flow does the currency formatting.

## Part 1 — Create the flow

1. Go to **make.powerautomate.com** → **Create** → **Scheduled cloud flow**.
   - Name: `Untapped Services Upsell Email`
   - Schedule: e.g. weekly, Monday 08:00 (use an **Instant/manual** trigger instead if you want to fire it by hand after refreshing the data).
2. **New step → Excel Online (Business) → "List rows present in a table"**
   - Location / Document Library / File: browse to your workbook
   - Table: `UpsellData`
3. On that action: **⋯ → Settings → Pagination = On, Threshold = 5000.**
   Without this the connector silently returns only the first 256 rows.
4. **New step → Data Operation → "Filter array"** (skips blank emails and reps with nothing untapped)
   - **From:** `value` (dynamic content from List rows)
   - Click **Edit in advanced mode** and paste:
     ```
     @and(not(empty(item()?['Email'])), greater(float(if(empty(item()?['Untracked Sum']),'0',item()?['Untracked Sum'])), 0))
     ```
5. **New step → Control → "Apply to each"**
   - **Select an output:** `Body` of Filter array
   - **⋯ → Settings → Concurrency control = On, Degree of parallelism = 1** (keeps sends orderly and avoids Outlook throttling).

## Part 2 — Compose actions inside the loop (formatting)

Add three **Compose** actions inside Apply to each and **rename them before continuing**
(⋯ → Rename). The names below are referenced later.

**`UntrackedFormatted`** — Inputs → fx:
```
formatNumber(float(if(empty(item()?['Untracked Sum']),'0',item()?['Untracked Sum'])), 'C0', 'en-US')
```

**`TrackedFormatted`** — Inputs → fx:
```
formatNumber(float(if(empty(item()?['Tracked Sum']),'0',item()?['Tracked Sum'])), 'C0', 'en-US')
```

**`TotalOpportunities`** — Inputs → fx:
```
add(add(if(empty(item()?['CC / Day 1 Upsell Count']),0,int(float(item()?['CC / Day 1 Upsell Count']))),if(empty(item()?['Low Pen Rate Count']),0,int(float(item()?['Low Pen Rate Count'])))),if(empty(item()?['No Services Op Count']),0,int(float(item()?['No Services Op Count']))))
```

Currency notes: `'C0'` + `'en-US'` → `$1,234,568`. Use `'en-GB'` for `£`, `'de-DE'` for `€`,
or a custom mask like `formatNumber(..., '£#,##0')`. `C0` = no decimals; use `C2` for pence/cents.

## Part 3 — Send the email

**New step (still inside the loop) → Office 365 Outlook → "Send an email (V2)"**

- **To:** dynamic content `Email` (from List rows)
- **Subject:** `Action needed: ` then insert `Outputs` of `UntrackedFormatted` then ` in untapped services opportunity`
- **Body:** click the **`</>` (code view)** toggle on the Body field, paste the entire contents of
  `HPE_Upsell_Merge_Template.html`, then replace each `{{placeholder}}` (select the token text,
  delete it, insert the dynamic content/expression in its place):

| Placeholder | Replace with | Occurrences |
|---|---|---|
| `{{UntrackedSum}}` | `Outputs` of **UntrackedFormatted** | 2 (headline + body) |
| `{{TrackedSum}}` | `Outputs` of **TrackedFormatted** | 1 |
| `{{TotalOps}}` | `Outputs` of **TotalOpportunities** | 1 |
| `{{CCDay1Count}}` | dynamic content `CC / Day 1 Upsell Count` | 1 |
| `{{LowPenCount}}` | dynamic content `Low Pen Rate Count` | 1 |
| `{{NoServicesCount}}` | dynamic content `No Services Op Count` | 1 |
| `{{CTALink}}` | type your dashboard/tracker URL | 1 |
| `{{SenderName}}` / `{{SenderTitle}}` | type the sender's name and job title | 1 each |

- Optional: **Show advanced options → Importance = High**.
- To send from a shared mailbox instead of your own, use **"Send an email from a shared mailbox (V2)"**.

## Part 4 — Test

1. Copy the workbook, replace all `Email` values with your own address, point the flow at the copy.
2. **Test → Manually → Run flow**, then check the run history: expand Apply to each to inspect each iteration's inputs/outputs.
3. Verify currency formatting, counts, the CTA link, and rendering in Outlook desktop + mobile.
4. Point the flow back at the live workbook and turn the schedule on.

## Gotchas

- **Excel connector returns every cell as text** — always wrap numeric columns in `float()`/`int()` inside expressions (already done above).
- **256-row default limit** — fixed by the pagination setting in Part 1 step 3.
- **Inline base64 images** (HPE logo, button end-caps, social icons): render fine in Outlook on the web / new Outlook, but **classic Outlook desktop and Gmail block `data:` URIs**. For production, upload the logo/icons to a public or intranet web location and swap each `src="data:image/png;base64,..."` for a hosted `https://` URL.
- **Blank count cells** render as empty text in the bullets. To force a `0`, replace the dynamic token with e.g. `if(empty(item()?['CC / Day 1 Upsell Count']),'0',item()?['CC / Day 1 Upsell Count'])`.
- **Outlook connector limits**: ~10,000 sends/day per mailbox; concurrency = 1 (Part 1 step 5) keeps bursts under control. For very large lists add a 5–10 s Delay action after the send.
- `Feedback Progress` and `Manager entitlement` aren't in the email; insert them anywhere in the body as dynamic content, or via `item()?['Feedback Progress']` / `item()?['Manager entitlement']`.

## Troubleshooting

**Every email contains the same row's data, repeated once per row in the table.**
Cause: when you insert Excel column tokens from the dynamic-content picker into the Send email
action while the loop iterates over the *Filter array* output, the designer can't tell those are
the same rows, so it silently wraps Send email in a second, nested **"Apply to each 1"** that
iterates over the original unfiltered table — re-sending the current outer row's Compose values
once per table row. Fix:
1. In the flow editor, look for a second loop ("Apply to each 1", or Send email sitting in its own loop). Delete the Send email action and that extra loop.
2. Re-add **Send an email (V2)** inside the *main* loop, after the three Compose actions.
3. Wire every field using **only the fx Expression tab** — never the dynamic-content picker for Excel columns — using the expressions below. Typed `item()` expressions never trigger auto-nesting.

| Field / placeholder | Expression (fx tab) |
|---|---|
| To | `item()?['Email']` |
| `{{TrackedSum}}` | `outputs('TrackedFormatted')` |
| `{{UntrackedSum}}` | `outputs('UntrackedFormatted')` |
| `{{TotalOps}}` | `outputs('TotalOpportunities')` |
| `{{CCDay1Count}}` | `if(empty(item()?['CC / Day 1 Upsell Count']),'0',item()?['CC / Day 1 Upsell Count'])` |
| `{{LowPenCount}}` | `if(empty(item()?['Low Pen Rate Count']),'0',item()?['Low Pen Rate Count'])` |
| `{{NoServicesCount}}` | `if(empty(item()?['No Services Op Count']),'0',item()?['No Services Op Count'])` |

If you renamed a Compose with spaces in the name, replace them with underscores in `outputs()`
(e.g. "Untracked Formatted" → `outputs('Untracked_Formatted')`).

**One count is blank in the email but correct in the total.** The body token for that column
either failed to insert (easy to do in code view) or points at a slightly different column name.
Replace it with the typed `if(empty(...))` expression from the table above. To confirm the exact
header text, open a finished run → **List rows present in a table → Show raw outputs** and copy
the JSON key exactly (watch for double/trailing spaces).

**Verify the fix:** run once, open 2–3 iterations of Apply to each in the run history and confirm
the Send email *inputs* differ per iteration.

## Optional: greeting by first name

There's no name column, but if emails follow `first.last@hpe.com` you can open the email with
"Hi Alex," using:
```
concat('Hi ', concat(toUpper(substring(first(split(item()?['Email'],'.')),0,1)), substring(first(split(item()?['Email'],'.')),1)), ',')
```
