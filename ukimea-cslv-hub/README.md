# UKIMEA CSLV HUB — Power Apps home screen

A homepage/landing screen for Power Apps that links out to four reporting
dashboards and shows each dashboard's live status. Styled with the
**HPE Design System, light theme** (values from the official
`hpe-design-tokens` package, v2.2.3 — the same data behind
[design-system.hpe.design/design-tokens/color-usage](https://design-system.hpe.design/design-tokens/color-usage)),
laid out following the HPE dashboard template pattern (page header, card
surfaces on a grey backdrop, status list).

## Files

| File | What it is |
|---|---|
| `UKIMEA-CSLV-Hub-HomeScreen.pa.yaml` | **The deliverable.** Paste-ready Power Apps YAML — every control on the screen. |
| `preview/ukimea-cslv-hub-preview.html` | Design preview. Open in a browser to see the layout, colours, and button hover behaviour before building in Power Apps. |

## How to build the screen in Power Apps

1. In [Power Apps](https://make.powerapps.com), create a **blank canvas app,
   Tablet format** (default 16:9, 1366 × 768 — the layout is designed for
   this size).
2. Open `UKIMEA-CSLV-Hub-HomeScreen.pa.yaml` and copy the **entire file**.
3. In Power Apps Studio, click on the empty screen canvas and press
   **Ctrl+V**. Studio understands YAML on the clipboard and recreates all
   the controls (background, header, four buttons, status board, credit).
4. Select each of `btnDash1`–`btnDash4` and replace
   `REPLACE_WITH_DASHBOARD_1_URL` … `_4_URL` in the `OnSelect` property
   with your real dashboard links, e.g.
   `Launch("https://app.powerbi.com/...")`.
5. Rename the button/status texts ("Dashboard 1" …) to the real dashboard
   names.

## Updating the status board

Each of the four rows is: **colour dot → dashboard name → reason
description → status badge**. Status is always shown as colour **plus** a
written word, so it stays readable for everyone (including colour-blind
users and print-outs).

To change a dashboard's status, set these three things on its row
(`crStatusDot n`, `lblStatusDesc n`, `btnStatusBadge n`):

| Status | Dot `Fill` (icon token) | Badge `Fill` (background token) | Badge `Text` |
|---|---|---|---|
| Working normally | `#009A71` (icon.ok) | `#D1FFEE` (background.ok) | `Operational` |
| Working but impaired | `#D36D00` (icon.warning) | `#FFF3DD` (background.warning) | `Degraded` |
| Not working | `#CC1F1A` (icon.critical) | `#FFECEC` (background.critical) | `Down` |
| Unknown | `#606A70` (icon.unknown) | `RGBA(0, 0, 0, 10)` (background.unknown) | `Unknown` |

…and write a one-line reason in the description label
(e.g. *"Unavailable – data gateway offline"*). Update `lblStatusUpdated`
with the current date/time when you make a change.

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
