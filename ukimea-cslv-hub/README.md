# UKIMEA CSLV HUB — Power Apps home screen

A homepage/landing screen for Power Apps that links out to six reporting
dashboards and shows each dashboard's live status. Styled with the
**HPE Design System, light theme** (values from the official
`hpe-design-tokens` package, v2.2.3 — the same data behind
[design-system.hpe.design/design-tokens/color-usage](https://design-system.hpe.design/design-tokens/color-usage)),
laid out following the HPE dashboard template pattern (page header, card
surfaces on a grey backdrop, status list), with an animated entrance,
idle motion, a personalised greeting, and a live clock.

## Files

| File | What it is |
|---|---|
| `UKIMEA-CSLV-Hub-HomeScreen.pa.yaml` | Classic edition. Paste-ready Power Apps YAML — every control on the screen, animations driven by Timer controls, statuses edited directly in the app. |
| `UKIMEA-CSLV-Hub-HomeScreen-SVG.pa.yaml` | **SVG + live Excel edition (recommended).** Same design rebuilt with SVG graphics — smoother 60 fps animations, an HPE-themed entrance — and the status board, badges, dots, ticker and button links all fed live from an Excel table. Setup steps below. |
| `preview/ukimea-cslv-hub-preview.html` | Design preview. Open in a browser to see the layout, colours, entrance/idle animations, and button hover behaviour before building in Power Apps. |

## SVG + live Excel edition

**Why SVG:** every visual (header, button cards, status card, dots) is an
Image control whose Image property is an inline SVG with its animations
written as CSS keyframes. They run at a smooth 60 fps, play even in
Studio's edit mode, and need no animation timers. Because an SVG can't
react to the mouse, each card has an invisible button on top that
supplies the hover green, pressed state, focus ring, tooltip and the
`Launch()`.

**The HPE-themed entrance:** the HPE "element" (the brand's green
rectangle outline) draws itself beside the title → brand stripe sweeps
across → each card's border traces itself in, its name rises, and a green
accent underline sweeps beneath it (staggered card by card) → the status
card outline draws and its separators grow in → the dots pop in.
**Idle:** a light shimmer crosses the brand stripe every 7 s and each dot
emits a radar "ping" ring in its status colour.

**Excel setup (do this BEFORE pasting):**

1. Put the workbook in **OneDrive for Business** (or SharePoint).
2. Select your data including headers → **Insert → Table** → on the
   *Table Design* tab rename the table to exactly **`DashboardStatus`**.
3. Columns, exactly: **Dashboard | Status | Text | URL**
   - `Dashboard` — must exactly match the six names shown in the app
     (the row labels are the lookup keys)
   - `Status` — `Operational`, `Limited` or `Down` (anything else shows grey)
   - `Text` — the one-line reason shown in the status board
   - `URL` — the link the dashboard's button opens
4. In Power Apps Studio: **Data pane → Add data → Excel Online
   (Business)** → sign in → pick the file → tick `DashboardStatus` →
   Connect.
5. Now paste `UKIMEA-CSLV-Hub-HomeScreen-SVG.pa.yaml` onto a blank
   Tablet screen. (Pasting before step 4 shows formula errors that clear
   once the table is connected.)

**How live is it:** the table is read when the app starts and re-pulled
every 5 minutes by `tmrRefresh` (change its `Duration` to alter the
cadence — value is in milliseconds). Excel is polled, not pushed, so an
edit appears on the next refresh, and the "Live from Excel · last
checked" caption shows when that was. Editing a row's Status in Excel
recolours the badge, the dot (and its ping), and the ticker entry, and
swaps the description — no app edits needed. Renaming a dashboard means
updating it in four places: the Excel `Dashboard` cell, the row label
(`lblStatusName n`), the SVG card (`imgDash n`) and its overlay button
(`btnDash n`).

## The six dashboards

| Button | OnSelect placeholder to replace |
|---|---|
| 1% Club | `REPLACE_WITH_1_PERCENT_CLUB_URL` |
| Attach Wizard [Beta] | `REPLACE_WITH_ATTACH_WIZARD_URL` |
| SFDC Hygiene | `REPLACE_WITH_SFDC_HYGIENE_URL` |
| UKIMEA Compute Backlog | `REPLACE_WITH_COMPUTE_BACKLOG_URL` |
| UKIMEA OS Channel Actuals | `REPLACE_WITH_OS_CHANNEL_ACTUALS_URL` |
| 3PAR EOSL Tracker | `REPLACE_WITH_3PAR_EOSL_URL` |

(The fourth name was truncated in the source screenshot — edit the `Text`
of `btnDash4` / `lblStatusName4` if the full name differs.)

## How to build the screen in Power Apps

1. In [Power Apps](https://make.powerapps.com), create a **blank canvas app,
   Tablet format** (default 16:9, 1366 × 768 — the layout is designed for
   this size).
2. Open `UKIMEA-CSLV-Hub-HomeScreen.pa.yaml` and copy the **entire file**.
3. In Power Apps Studio, click on the empty screen canvas and press
   **Ctrl+V**. Studio understands YAML on the clipboard and recreates all
   the controls (timers, background, header, six buttons, status board,
   credit).
4. Select each of `btnDash1`–`btnDash6` and replace the placeholder in the
   `OnSelect` property with the real link, e.g.
   `Launch("https://app.powerbi.com/...")`.

**If you edit the YAML by hand:** any formula or text containing a colon
followed by a space (e.g. `With({p: ...})`, `"Last updated: ..."`) must sit
on its own line under a `|-` marker, the way the file already formats them.
Putting one back on the same line as its property name makes Power Apps
reject the paste with error PA1001 `YamlInvalidSyntax`.

## Animations & extras

Everything is driven by three invisible **Timer** controls (Power Apps'
native way to animate — no add-ins needed):

- **Entrance cascade** (`tmrEntrance`, one-shot, ~1.5 s): the HPE-green
  brand stripe sweeps across the top, the title and greeting fade in, the
  six buttons rise and fade in one after another (left-to-right,
  top-to-bottom), then the status board and its rows follow, and finally
  the credit. Easing is a cubic ease-out for that soft HPE-style landing.
  When the timer ends it sets `varLoaded`, which pins every control to its
  final state (so nothing ever re-animates or flickers afterwards).
- **Idle motion** (`tmrIdle`, 4 s loop): the six status dots gently
  "breathe" (opacity oscillates via a sine wave), which makes the board
  read as live without being distracting.
- **Live clock** (`tmrClock`, 1 s tick): sets `varNow`, which feeds the
  date/time readout in the header.
- **Personalised greeting**: "Good morning / afternoon / evening, {first
  name}" from `User().FullName` — it greets whoever opens the app.
- **Stock-exchange status ticker** (`htmlTicker`): a dark band pinned to
  the bottom of the screen where every dashboard's name and status scroll
  continuously, NYSE-style — ▲ green for Operational, ◆ amber for
  Limited, ▼ red for Down, ● grey for anything else (HPE dark-theme
  status tokens on `background.neutral.xstrong`). The ticker's HTML is
  **generated from the status board's own controls** (`lblStatusName n` /
  `btnStatusBadge n`), so updating a badge automatically re-words and
  re-colours the ticker — you never edit it directly. Scroll speed is the
  `scrollamount` attribute in `htmlTicker.HtmlText` (higher = faster).
  It scrolls via the HTML `<marquee>` element — long-deprecated but still
  supported by every browser Power Apps runs in, and the standard
  community technique for ticker text in canvas apps. If it ever stops
  scrolling in a future browser, the fallback is a Timer-driven label
  (same look, slightly choppier motion) — ask and it can be swapped in.
- **Micro-interactions**: buttons change colour on hover (white →
  HPE primary green) and darken again while pressed; tooltips and
  accessible labels on every link; a visible keyboard-focus ring using
  HPE's `color.focus`; the preview's ticker pauses on hover.

**Edit mode vs Preview:** timers only run in Preview (F5) and the
published app. In Studio's edit mode the screen simply shows its
finished resting state — every animation formula falls back to "fully
visible" while `tmrEntrance` hasn't started.

**Tuning:** entrance timing lives in the `With({p: ...})` formulas — the
first number is the control's start delay (ms), the second is its duration.
`tmrIdle.Duration` sets the breathing speed. **Removing motion:** delete
the three timers and replace each `With(...)` formula with its resting
value (the README table below has the colours). The HTML preview also
respects the OS "reduced motion" accessibility setting.

## Updating the status board

Each of the six rows is: **colour dot → dashboard name → reason
description → status badge**. Status is always shown as colour **plus** a
written word, so it stays readable for everyone (including colour-blind
users and print-outs).

To change a dashboard's status, set these three things on its row
(`crStatusDot n`, `lblStatusDesc n`, `btnStatusBadge n`):

| Status | Dot colour (icon token) | Badge `Fill` (background token) | Badge `Text` |
|---|---|---|---|
| Working normally | `RGBA(0, 154, 113, …)` — icon.ok `#009A71` | `RGBA(209, 255, 238, …)` — background.ok `#D1FFEE` | `Operational` |
| Working but impaired | `RGBA(211, 109, 0, …)` — icon.warning `#D36D00` | `RGBA(255, 243, 221, …)` — background.warning `#FFF3DD` | `Limited` |
| Not working | `RGBA(204, 31, 26, …)` — icon.critical `#CC1F1A` | `RGBA(255, 236, 236, …)` — background.critical `#FFECEC` | `Down` |
| Unknown | `RGBA(96, 106, 112, …)` — icon.unknown `#606A70` | `RGBA(0, 0, 0, 10)` — background.unknown | `Unknown` |

Because the dot and badge fills are animated, change only the **RGB
numbers** inside the existing `RGBA(...)` in each formula and leave the
alpha expression (the `p * (...)` / `p` part) as it is.

…then write a one-line reason in the description label
(e.g. *"Unavailable – data gateway offline"*) and update
`lblStatusUpdated` with the current date/time.

## HPE light-theme tokens used

| Role | Token | Value |
|---|---|---|
| Page background | `hpe.color.background.back` | `#F7F7F7` |
| Card / header surface | `hpe.color.background.front` | `#FFFFFF` |
| Brand accent stripe | `hpe.color.decorative.brand` | `#01A982` |
| Headings & button text | `hpe.color.text.strong` / `text.heading` | `#292D3A` |
| Body text (on status badges) | `hpe.color.text.default` | `#3E4550` |
| Supporting text & credit | `hpe.color.text.weak` | `#606A70` |
| Card borders | `hpe.color.border.weak` | `#D4D8DB` |
| Button hover fill | `hpe.color.background.primary.strong` | `#068667` |
| Button pressed fill | `hpe.color.background.primary.strong.hover` | `#006750` |
| Text on hovered button | `hpe.color.text.onPrimaryStrong` | `#FFFFFF` |
| Keyboard focus ring | `hpe.color.focus` | `#292D3A` |
| Card radius | `hpe.radius.medium` | `12px` |
| Badge radius | `hpe.radius.full` | pill |

Row separators use HPE base grey-200 (`#E6E8E9`) for a hairline that sits
one step lighter than `border.weak`.

*Note on fonts: the HPE brand font (Metric) isn't available inside Power
Apps, so the screen uses Open Sans — Power Apps' default — as the closest
clean sans-serif. The HTML preview will pick up Metric automatically on
machines that have it installed.*

---

**Dashboard architects:** Ben Robertson · Alex Cohen
