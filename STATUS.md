# Where this project is up to

**Last updated:** after Phase 2
**Current position:** Phase 2 complete. Phase 3 not started.

> ⚠️ **Opening hours in `src/data/restaurant.ts` are unconfirmed placeholders.** A yellow
> warning bar shows on every page while you develop, and disappears from the built site.
> When the owner confirms the real hours, update that file and set `hoursConfirmed = true`.

## Getting back to work after a break

```
cd ~/projects/la-casa
npm run dev
```

Then open http://localhost:4321. `Ctrl + C` stops the server. No need to re-clone or re-run
`npm install` — that is already done.

## How to work out where you are, without asking

| Command | What it tells you |
| --- | --- |
| `git log --oneline -3` | The newest commit message names the last phase finished |
| `git status` | Whether you left half-finished edits lying around |
| `ls src/data` | Missing = Phase 2 not started. Present = Phase 2 underway or done |
| `ls src/pages` | How many pages exist. Phase 1 = just `index.astro` |

## Phase checklist

- [x] **Phase 1 — Project runs.** Astro 7.1.6, builds clean, placeholder homepage at
      `localhost:4321`.
- [x] **Phase 2 — Single source of truth.** `src/data/restaurant.ts` holds hours, phone,
      address, email. Header and footer render from it. Live "Open now / Closed" badge,
      correct in Weybridge time regardless of the visitor's timezone.
- [ ] **Phase 3 — Homepage.** Palette, fonts, hero, Book a Table button, mobile-first.
- [ ] **Phase 4 — Menu page.** `src/data/menu.ts`, jump links per course, dietary markers.
- [ ] **Phase 5 — Demo live.** Netlify, `noindex`, shareable URL. The sales asset.
- [ ] **Phase 6 — Remaining pages.** About, Book, Takeaway, Contact + map, Privacy.
- [ ] **Phase 7 — Booking.** resOS embed. Demo mode until they sign.
- [ ] **Phase 8 — SEO.** Meta descriptions, Restaurant + Menu schema, sitemap, robots, 404.
- [ ] **Phase 9 — Analytics + cookies.** Cookieless, so no consent banner needed.
- [ ] **Phase 10 — Images + speed.** Gallery, optimisation, Lighthouse 90+.
- [ ] **Phase 11 — Pitch pack.** Before/after, evidence list, proposal.

Full detail for every phase is in `PLAN.md`.

## Outstanding on the pitch side (not code)

These are from `PLAN.md` §0 and are still unverified:

- [ ] Screenshot proving the opening hours contradict each other — **the strongest point you
      have, and still unevidenced**
- [ ] `curl -sI http://www.la-casa-weybridge.com/ | grep -iE "^HTTP|^location"` — does http
      redirect to https? Decides how hard you can push the security angle
- [ ] Count of genuinely insecure links (command in `PLAN.md` §0)
- [ ] Whether any page has a meta description
