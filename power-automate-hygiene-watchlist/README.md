# SFDC Hygiene Watchlist — weekly manager email

Every **Monday at 10:00** this flow sends **one person** (always the same
recipient) an HPE-branded summary of the sellers with SFDC hygiene issues:

- **Three KPI tiles:** sellers with flags (of all in scope), opps flagged
  (of all in scope), and team hygiene %.
- **A watchlist table**, lowest hygiene first: one row per seller with at
  least one flagged opp, showing the seller's name (a mailto link, so the
  recipient can email them in one click), flagged opps as "3 of 12", and a
  green hygiene-score bar with the %.
- A **Hygiene Hub** button that opens the Power BI report.
- On a week with no flags at all, the table shows a "Clean sweep" message
  instead.

| File | Purpose |
|---|---|
| `watchlist-query.dax` | Query text for the Power BI action |
| `email-body-template.html` | Tokenized email body (paste into a Compose action) |
| `preview/sample-email.html` | The email rendered with sample data |

### How this differs from the team email (`../power-automate-hygiene-email`)

- **Fixed recipient:** the To field is a typed-in address, not built from the
  query.
- **New query:** this one returns flagged and total opp counts per seller,
  plus team totals, which the champions query doesn't. Use
  `watchlist-query.dax` here, not `hygiene-scores.dax`.
- **The same report filters**, including `Current Quarter Filter`, and the
  same rule: the `Is Hygiene flag? = Y` page filter is deliberately **not**
  applied.

---

## Build the flow

Create a new **Scheduled cloud flow** and give it a name such as
*SFDC Hygiene Watchlist*. Rename each action to **exactly** the names below
before you paste expressions, because expressions refer to actions by name
(with spaces replaced by underscores, e.g. `outputs('Team_stats')`).

As in the first flow, every expression below goes in through the
**expression editor** (the *fx* button), not typed as plain text.

### 1. Trigger — Recurrence
- **Frequency:** Week, **Interval:** 1
- **On these days:** Monday, **At these hours:** 10, **At these minutes:** 0
- **Time zone:** the same one you used in the team email flow.

### 2. `Run watchlist query` — Power BI ▸ *Run a query against a dataset*
- **Workspace / Dataset:** the same semantic model as the team email
- **Query text:** paste the whole of [`watchlist-query.dax`](watchlist-query.dax)

### 3. Condition (guard)
- **Left:** `length(outputs('Run_watchlist_query')?['body/firstTableRows'])`
- **Operator:** is equal to, **Right:** `0`
- **True** branch: add **Terminate** (Status: *Succeeded*).
- Steps 4–9 all go in the **False** branch.

This stops an empty email if the query ever returns nothing.

### 4. `Team stats` — Data Operation ▸ *Compose*
- **Inputs:**
  ```
  first(outputs('Run_watchlist_query')?['body/firstTableRows'])
  ```
  The team totals are repeated on every row of the query result. This picks
  up the first row so the next steps can read them.

### 5. `Filter sellers with issues` — Data Operation ▸ *Filter array*
- **From:**
  ```
  outputs('Run_watchlist_query')?['body/firstTableRows']
  ```
- **Condition:** click *Edit in advanced mode* and paste:
  ```
  @greater(item()?['[FlaggedOpps]'], 0)
  ```
  The query already sorts lowest hygiene first, and the filter keeps that
  order.

### 6. `Select watchlist rows` — Data Operation ▸ *Select*
- **From:**
  ```
  body('Filter_sellers_with_issues')
  ```
- **Map:** switch to **text mode** (the toggle on the right of the Map field)
  and insert this expression. It builds one table row per seller: name with a
  mailto link, flagged opps, and the hygiene bar with its %:
  ```
  concat('<tr><td style="padding: 10px 16px; border-bottom: solid 1px #E0E0E0; font-family: Arial,Helvetica,sans-serif; font-size: 10.5pt; line-height: 14pt;"><a href="mailto:', coalesce(item()?['[SpecialistEmail]'], ''), '?subject=SFDC%20hygiene%20follow-up" style="color: #000000; font-weight: bold; text-decoration: underline;">', item()?['[SpecialistName]'], '</a></td><td style="padding: 10px 8px; border-bottom: solid 1px #E0E0E0; font-family: Arial,Helvetica,sans-serif; font-size: 10.5pt; line-height: 14pt; color: #000000;"><strong>', string(item()?['[FlaggedOpps]']), '</strong> of ', string(item()?['[TotalOpps]']), '</td><td style="padding: 10px 16px 10px 8px; border-bottom: solid 1px #E0E0E0;"><table cellpadding="0" cellspacing="0"><tr><td width="160" height="10" bgcolor="#E3E6E8" style="font-size: 0; line-height: 0;">', if(greater(item()?['[BarPx]'], 0), concat('<table width="', string(item()?['[BarPx]']), '" cellpadding="0" cellspacing="0"><tr><td height="10" bgcolor="#01A982" style="font-size: 0; line-height: 0;">&nbsp;</td></tr></table>'), '&nbsp;'), '</td><td width="10" style="font-size: 0; line-height: 0;">&nbsp;</td><td width="42" align="right" style="font-family: Arial,Helvetica,sans-serif; font-size: 10.5pt; font-weight: bold; color: #000000;">', string(item()?['[HygienePct]']), '%</td></tr></table></td></tr>')
  ```
  The bar is a 160px light-gray track with a green fill `BarPx` wide. A seller
  at 0% gets an empty track; Outlook would draw a zero-width fill as a sliver,
  so it is left out.

### 7. `Compose email template` — Data Operation ▸ *Compose*
- **Inputs:** paste the entire contents of
  [`email-body-template.html`](email-body-template.html). There's nothing to
  edit first: the Hygiene Hub link is already set.

### 8. `Compose email body` — Data Operation ▸ *Compose*
- **Inputs:** this single expression, pasted as one line:
  ```
  replace(replace(replace(replace(replace(replace(replace(outputs('Compose_email_template'), '{{RUN_DATE}}', formatDateTime(convertFromUtc(utcNow(), 'GMT Standard Time'), 'MMMM d, yyyy')), '{{ISSUE_SELLERS}}', string(outputs('Team_stats')?['[TeamSellersWithIssues]'])), '{{TOTAL_SELLERS}}', string(outputs('Team_stats')?['[TeamSellers]'])), '{{FLAGGED_OPPS}}', string(outputs('Team_stats')?['[TeamFlaggedOpps]'])), '{{TOTAL_OPPS}}', string(outputs('Team_stats')?['[TeamTotalOpps]'])), '{{TEAM_HYGIENE}}', string(outputs('Team_stats')?['[TeamHygienePct]'])), '{{WATCHLIST_ROWS}}', if(greater(length(body('Filter_sellers_with_issues')), 0), join(body('Select_watchlist_rows'), ''), '<tr><td colspan="3" style="padding: 16px; font-family: Arial,Helvetica,sans-serif; font-size: 10.5pt; line-height: 14pt; color: #000000;">&#127881; <strong>Clean sweep!</strong> No seller has a flagged opportunity this week.</td></tr>'))
  ```
  Replace `'GMT Standard Time'` with the Windows time-zone name you used in
  the team email flow (e.g. `'Central Standard Time'`).

### 9. Send — Office 365 Outlook ▸ *Send an email (V2)*
- **To:** type the recipient's email address directly (plain text, no
  expression). Add a semicolon and a second address if you'd like a copy
  yourself, or use **CC** under *Show advanced options*.
- **Subject** (expression):
  ```
  concat('SFDC Hygiene Watchlist — ', string(outputs('Team_stats')?['[TeamSellersWithIssues]']), ' seller(s) flagged — ', formatDateTime(convertFromUtc(utcNow(), 'GMT Standard Time'), 'MMMM d, yyyy'))
  ```
  (Same time-zone swap as step 8.)
- **Body:** click the `</>` code-view icon in the Body field, then insert the
  expression `outputs('Compose_email_body')`.

### 10. Test
For the first run, put **your own address** in To. Then **Test ▸ Manually**
and check:

1. *Run watchlist query* → raw outputs: every in-scope seller is listed, and
   the team totals look right.
2. The KPI tiles match the report (team hygiene ≈ the report's overall
   hygiene with only the non-hygiene-flag filters applied).
3. Every seller in the table has at least 1 flagged opp, and the order runs
   from lowest score upwards.

Once it looks right, switch To back to the real recipient and save.

---

## Customizing

- **Sort by most flagged opps instead of lowest %:** in the DAX, change the
  last line to
  `ORDER BY [FlaggedOpps] DESC, [HygienePct] ASC, [SpecialistName] ASC`.
- **Only list sellers below a threshold** (e.g. under 90%): change the
  *Filter sellers with issues* condition to
  `@and(greater(item()?['[FlaggedOpps]'], 0), less(item()?['[HygienePct]'], 90))`.
  The KPI tiles still count the whole team.
- **Different day or time:** edit the Recurrence trigger, and update the
  "every Monday at 10:00" footer line in the template to match.

## Troubleshooting

- **400 Bad Request, "Column … cannot be found"**: a column name in the
  DAX doesn't match the model. The query uses the same names as the team
  email's working query, so compare the two if you've renamed anything.
- **A seller shows 99% but is on the watchlist**: this is intended.
  Percentages are rounded *down*, so one flagged opp out of 150 shows 99%
  rather than a misleading 100%.
- **The table is empty but the tiles say sellers have flags**: check that
  step 6's *From* is `body('Filter_sellers_with_issues')` and that the action
  names match exactly (`Select_watchlist_rows` in step 8).
- **Bars show up but have no color in the Outlook desktop app**: make sure
  the expression was pasted unchanged. The colors come from the `bgcolor`
  attributes, which Outlook's renderer needs.
- **Rows look like `{"[SpecialistName]": …}` or empty**: the JSON keys must
  include the square brackets, e.g. `item()?['[SpecialistName]']`.
