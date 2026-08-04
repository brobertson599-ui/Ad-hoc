# La Casa, Weybridge — website

Static site built with [Astro](https://astro.build). Pitch/demo build — see `PLAN.md`.

## Running it locally

Needs Node.js (LTS) and npm installed.

```
npm install
npm run dev
```

Then open http://localhost:4321 — the page reloads as you save files. `Ctrl + C` stops it.

## Other commands

| Command | What it does |
| --- | --- |
| `npm run build` | Produces the finished site in `dist/` — what gets published |
| `npm run preview` | Serves `dist/` so you can check the built site before deploying |
| `npm audit` | Lists known security problems in the code libraries. Should say `found 0 vulnerabilities` |

## Where content lives

| File | Contains |
| --- | --- |
| `src/pages/` | One file per page of the site |
| `src/data/restaurant.ts` | Hours, phone, address, email — added in Phase 2 |
| `src/data/menu.ts` | Every dish, price and dietary marker — added in Phase 4 |

Opening hours and menu items are defined **once** in `src/data/` and rendered everywhere from
there. Never hard-code an opening time or a price into a page.
