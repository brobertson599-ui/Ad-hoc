# SFDC Hygiene Weekly — Power Automate email automation

Every **Monday at 10:00** this flow:

1. Queries the Power BI semantic model table **`Opp Id Break Down`** for every
   IB specialist's name (`IB specialist`), email (`IB email`) and hygiene score
   (the `Hygiene by seller` logic: share of opps with `Is Hygiene flag? = "Y"`).
2. Treats a score of **0** as **100% hygiene** (no flagged opps).
3. Sends one HPE-branded email to **all** IB specialists that politely reminds
   everyone why SFDC hygiene matters, **@-mentions** the 100% club in the body,
   and shows a **champions card**: a hero count plus one row per champion with
   a trophy, their name, a full HPE-green progress bar, and "100%".

| File | Purpose |
|---|---|
| `hygiene-scores.dax` | Query text for the Power BI action |
| `email-body-template.html` | Tokenized HPE-style email body (paste into a Compose action) |
| `preview/sample-email.html` | The email rendered with sample data, for review |

---

## Prerequisites

- A **Power BI Pro** (or PPU/Fabric) license and **Build permission** on the
  dataset that contains `Opp Id Break Down`.
- The **Power BI** and **Office 365 Outlook** connectors available in your
  Power Automate environment.
- Columns assumed on `'Opp Id Break Down'`: `IB specialist`, `IB email`,
  `Is Hygiene flag?`, `Is Relevant Op?`, `Manager`, `Services Call`. If your
  actual column names differ, edit them in `hygiene-scores.dax` only — the
  flow expressions never reference raw column names.

> **Important — one filter you must NOT copy:** the report page filters
> include `Is Hygiene flag? is Y`. That is only a *display* filter for the
> page's visuals. Applying it to the score query would make every remaining
> row flagged (everyone at 0% hygiene). The query in `hygiene-scores.dax`
> replicates the *other* filters (`Is Relevant Op? = Y`, `Manager` not blank,
> `Services Call` not blank) and leaves a marked TODO for the locked
> **Current Quarter** filter — point it at whatever field that filter uses in
> your model.

---

## Build the flow

Create a **Scheduled cloud flow**. Rename each action to **exactly** the names
below before pasting expressions — expressions reference actions by name
(spaces become underscores, e.g. `outputs('Run_hygiene_query')`).

### 1. Trigger — Recurrence
- **Frequency:** Week, **Interval:** 1
- **On these days:** Monday, **At these hours:** 10, **At these minutes:** 0
- **Time zone** (under *Show advanced options*): pick yours, e.g.
  `(UTC) Dublin, Edinburgh, Lisbon, London` or
  `(UTC-06:00) Central Time (US & Canada)`.

### 2. `Run hygiene query` — Power BI ▸ *Run a query against a dataset*
- **Workspace / Dataset:** the semantic model containing `Opp Id Break Down`
- **Query text:** paste the whole of [`hygiene-scores.dax`](hygiene-scores.dax)

The action returns the rows under `body/firstTableRows`; each row is JSON like
`{"[SpecialistName]": "…", "[SpecialistEmail]": "…", "[HygieneScore]": 0.25}`
(the bracketed keys are the aliases from the query's `SELECTCOLUMNS`).

### 3. (Optional guard) — Condition
If `length(outputs('Run_hygiene_query')?['body/firstTableRows'])` **is equal to** `0`
→ **Terminate** (status *Succeeded*). Prevents an empty blast if the query
ever returns nothing.

### 4. `Select all emails` — Data Operation ▸ *Select*
- **From:**
  ```
  outputs('Run_hygiene_query')?['body/firstTableRows']
  ```
- **Map:** switch to **text mode** (the small `T`/toggle icon on the right of
  the Map field) and enter:
  ```
  item()?['[SpecialistEmail]']
  ```

### 5. `Filter Champions` — Data Operation ▸ *Filter array*
- **From:**
  ```
  outputs('Run_hygiene_query')?['body/firstTableRows']
  ```
- **Condition:** click *Edit in advanced mode* and paste:
  ```
  @equals(float(coalesce(item()?['[HygieneScore]'], 1)), 0)
  ```
  (score `0` = zero flagged opps = 100% hygiene; a missing score is treated
  as "not a champion").

### 6. `Select champion mentions` — Data Operation ▸ *Select*
- **From:**
  ```
  body('Filter_Champions')
  ```
- **Map (text mode):**
  ```
  concat('<a href="mailto:', item()?['[SpecialistEmail]'], '" style="color: #0072C6; text-decoration: none; font-weight: bold;">@', item()?['[SpecialistName]'], '</a>')
  ```
  This renders each champion as a blue, bold, clickable **@Name** — the
  closest an automated email can get to an Outlook mention (native
  "@mentions" cannot be injected by the connector; the champions are also in
  the To line, which is what a real mention does anyway).

### 7. `Select champion rows` — Data Operation ▸ *Select*
- **From:**
  ```
  body('Filter_Champions')
  ```
- **Map (text mode)** — builds one champions-card row (trophy, name, full
  green bar, 100%):
  ```
  concat('<tr><td style="padding: 8px 20px; border-bottom: solid 0.5pt #E0E0E0;"><table width="100%" cellpadding="0" cellspacing="0"><tr><td width="24" style="font-size: 12pt; line-height: 12pt;">&#127942;</td><td style="font-family: Arial,Helvetica,sans-serif; font-size: 10.5pt; font-weight: bold; color: #000000; line-height: 14pt;">', item()?['[SpecialistName]'], '</td><td width="170" style="padding: 0 10px;"><table width="100%" cellpadding="0" cellspacing="0"><tr><td bgcolor="#01A982" height="10" style="font-size: 0; line-height: 0;">&nbsp;</td></tr></table></td><td width="42" align="right" style="font-family: Arial,Helvetica,sans-serif; font-size: 10.5pt; font-weight: bold; color: #000000;">100%</td></tr></table></td></tr>')
  ```

### 8. `Compose email template` — Data Operation ▸ *Compose*
- **Inputs:** paste the entire contents of
  [`email-body-template.html`](email-body-template.html).
  First set the two edit-once placeholders (`[SENDER NAME]`,
  `[SENDER JOB TITLE]`) and the CTA button's SFDC link.

### 9. `Compose email body` — Data Operation ▸ *Compose*
- **Inputs:** a single expression (paste as one line):
  ```
  replace(replace(replace(replace(outputs('Compose_email_template'), '{{RUN_DATE}}', formatDateTime(convertFromUtc(utcNow(), 'GMT Standard Time'), 'MMMM d, yyyy')), '{{CHAMPION_COUNT}}', string(length(body('Filter_Champions')))), '{{SHOUTOUT_LINE}}', if(greater(length(body('Filter_Champions')), 0), concat('A huge congratulations and thank you to our specialists with a perfect scorecard this week: ', join(body('Select_champion_mentions'), ', '), '. Zero hygiene flags &mdash; you set the standard for the whole team!'), 'No one reached 100% this week &mdash; let''s change that! A few minutes of SFDC housekeeping today puts your name up in lights next Monday.')), '{{CHAMPION_ROWS}}', if(greater(length(body('Filter_Champions')), 0), join(body('Select_champion_rows'), ''), '<tr><td style="padding: 12px 20px; font-family: Arial,Helvetica,sans-serif; font-size: 10.5pt; color: #000000;">&#128064; This spot is reserved for you &mdash; clear your hygiene flags to join the club!</td></tr>'))
  ```
  Replace `'GMT Standard Time'` with the same time zone you chose in the
  trigger (Windows time-zone names, e.g. `'Central Standard Time'`,
  `'Eastern Standard Time'`, `'Central Europe Standard Time'`).

### 10. Send — Office 365 Outlook ▸ *Send an email (V2)*
- **To** (expression — deduplicated, semicolon-separated):
  ```
  join(union(body('Select_all_emails'), body('Select_all_emails')), ';')
  ```
- **Subject** (expression):
  ```
  concat('🏆 SFDC Hygiene Weekly — ', formatDateTime(convertFromUtc(utcNow(), 'GMT Standard Time'), 'MMMM d, yyyy'))
  ```
- **Body:** click the `</>` code-view icon in the Body field, then insert the
  expression `outputs('Compose_email_body')`.
- Optional: use *Send an email from a shared mailbox (V2)* so the mail comes
  from a team address instead of your own.

### 11. Test
Save, then **Test ▸ Manually**. Check: the query returned rows, the champion
count matches your report (with the Current Quarter filter applied), and the
email renders correctly in Outlook desktop + web.

---

## How the "graphic" works (and alternatives)

Outlook's desktop client renders email with Word's engine: no scripts, no
external CSS, `data:` image URIs blocked, external images blocked by default.
So the champions visual is built entirely from **tables and background
colors** — it renders instantly for every recipient with nothing to download:

- a white card with an HPE-green top rule,
- a hero number (count of champions) in HPE green,
- one row per champion: 🏆 + **name** + a **full-width #01A982 progress bar** + **100%**.

Considered alternatives, if you'd like to upgrade later:

- **Export a real Power BI visual** (Power BI ▸ *Export To File for Power BI
  Reports* → attach/embed a PNG of an actual report page). Looks great, but
  needs Premium/Fabric capacity and recipients must click "download images".
- **Badge wall / pills** (a chip per name): reads nicely but wrapping chips
  aren't reliable in Outlook's renderer — the row layout is the safe version.
- **Streak tracking** (e.g. "🏆 ×3 — third week running!"): needs the flow to
  write each week's champions to a SharePoint list/Excel table first — happy
  to build that as a v2.

## Troubleshooting

- **Expression can't find a value / rows are empty objects** — the JSON keys
  from the Power BI action must match the `SELECTCOLUMNS` aliases *including
  brackets*: `item()?['[SpecialistName]']`. If you rename aliases in the DAX,
  update the three Select/Filter expressions.
- **Champion list doesn't match the report** — the Current Quarter TODO in
  `hygiene-scores.dax` is probably still commented out, or your report page
  has extra slicers/filters not replicated in the query. Compare against the
  report with *only* the non-hygiene-flag filters applied.
- **Everyone shows as flagged / no champions ever** — check you did not add
  the `Is Hygiene flag? = Y` page filter into the query (see the warning at
  the top).
- **`SummarizeColumns` errors** — usually a misspelled table/column name;
  names with spaces must keep their single quotes: `'Opp Id Break Down'[IB email]`.
- **Duplicate or missing recipients** — recipients come from distinct
  `IB email` values in the query result; blanks are filtered out in the DAX.
