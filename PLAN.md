# La Casa, Weybridge — Rebuild Plan

Prepared for a cold-outreach pitch. Demo-first build.

---

## 0. Before anything: verify the claims you plan to pitch with

**Rule, before any of this: look, do not probe.** Reading page source and a published
sitemap is ordinary browsing and entirely legitimate. Running a vulnerability scanner, an
exploit, or a login attempt against a server you do not own is an offence under the Computer
Misuse Act 1990 — regardless of good intentions, and regardless of whether it "worked". It
would also end any prospect of the relationship. Every finding below came from View Source.
Keep it that way.

### Confirmed by page source (screenshots on file, 4 Aug 2026)

- `<meta name="generator" content="Powered by Slider Revolution 5.4.6.4">` — the plugin is
  there **and the site publicly announces its exact version**, so it can be found by anyone
  scanning for that version without any probing at all. 5.4.6.4 dates to 2018 and sits below
  every fixed version in the public vulnerability database.
- `<meta name="generator" content="WordPress 6.2.2" />` — WordPress core itself, released
  May 2023. This is the bigger finding: it is not one stale plugin, it is a whole install
  frozen for about three years, missing every core security release since.
- `<meta name="generator" content="Site Kit by Google 1.68.0" />` and the `twentyseventeen`
  theme — same era, same neglect.
- `<a href="http://www.la-casa-weybridge.com/wp-content/upl…">Drinks menu</a>` — a genuine
  insecure internal link to their own content.
- The menus are PDFs sitting in `wp-content/uploads`, consistent with the 2022 dating.

### Refuted — remove these from the pitch

- **"The menu page's canonical URL is http://"** — it is not. The source shows
  `<link rel="canonical" href="https://www.la-casa-weybridge.com/house-menu/" />`. Drop this
  claim entirely.
- **"There is no sitemap"** — there is. `/sitemap.xml` returns 404, which is what my original
  check looked for, but WordPress core serves its own at `/wp-sitemap.xml`, listing four
  sub-sitemaps. Reframe (see Appendix point 6); do not claim it is missing.

### Still unverified — and one of them is the whole pitch

**1. The hours contradiction.** Nothing yet proves this, and it is the single most valuable
point you have. Screenshot the homepage, the booking page and a page footer in one image.

**2. Does `http://` redirect to `https://`?** This decides how hard you can push the security
angle:

```
curl -sI http://www.la-casa-weybridge.com/ | grep -iE "^HTTP|^location"
```

If you see `301` and a `Location:` starting `https://`, the insecure links repair themselves
when clicked — the point drops to a hygiene issue and you must stop calling it "half your
site loads insecurely". If there is no redirect, it stays a real finding.

**3. Counting the insecure links properly.** "HTTP appeared 15 times" over-counts: `https://`
contains `http` as a substring, and some matches will be `http://www.w3.org/…` namespace
identifiers, which are labels rather than links and are harmless. This counts only genuine
insecure URLs pointing at their own site:

```
curl -s https://www.la-casa-weybridge.com/house-menu/ | grep -o 'http://[^"]*' | grep la-casa | sort -u
```

The number of lines that prints is the number you can defend. Note the `/wp-content/uploads/`
date folder in those paths — it timestamps the PDFs for you.

**4. Meta descriptions.** Confirms the SEO point:

```
curl -s https://www.la-casa-weybridge.com/house-menu/ | grep -i 'name="description"'
```

No output means no meta description on that page.

Keep the screenshots. They are the pitch.

---

## 1. Recommended stack

**Astro (static site generator) + site data in one file + free hosting on Netlify.**

A static site generator turns your HTML/CSS plus a data file into finished pages at build
time, so the menu and hours exist in one place in the code and get printed into every page
automatically.

- **Your skill level.** Astro pages are HTML files with a small block of JavaScript at the
  top. If you can write HTML and CSS, you can write Astro on day one; you learn the extra
  bits as you need them. Nothing here needs React, a database or a server.
- **Your budget.** Hosting £0. HTTPS £0 and automatic. The only unavoidable running cost is
  the domain (~£10–12/year, and the client already owns theirs). Total well under £15/month.
- **Who maintains it — the heavily weighted one.** You do; the client will not touch the
  code. That single fact means **you should not install a CMS**, and the brief's warning
  ("a static site with no CMS is the wrong answer") does not apply here — it applies when a
  non-technical client edits their own content. Menu items and opening hours live in two
  data files. To change a price you open that file on github.com in a browser, edit the
  line, click "Commit changes", and the live site rebuilds itself in about 60 seconds. No
  terminal, no npm, no deploy to think about — genuinely a two-minute job from a phone. If
  the client later wants to edit things themselves, you bolt Sveltia CMS on top of the same
  files without restructuring anything.

**Runner-up: Eleventy.** Same shape, same price, equally sound. Rejected for one reason:
Astro ships image optimisation and sitemap generation in the box, and Eleventy makes you
assemble those yourself — glue you do not want to be debugging as your first project.

**Explicitly rejected: WordPress.** It is the thing that broke their current site. Putting
them back on a platform that needs monthly security patching, on a retainer where you are
the one liable for the patching, recreates the exact problem you are pitching against. A
static site has no database, no login page and no plugins, so there is nothing to hack.

---

## 2. Prerequisites checklist

Do all five before Phase 1. Each has a verification command and the output you should see.

**1. Node.js (LTS version)** — the engine that runs the build tool.

- macOS / Windows: download the LTS installer from https://nodejs.org and run it, accepting
  every default.
- Verify:
  ```
  node -v
  ```
  Expect something like `v24.4.1`. Any `v20` or higher is fine. `command not found` means
  the installer did not finish, or you need to close and reopen your terminal.

**2. npm** — installs code libraries; it comes bundled with Node, nothing to install.

- Verify:
  ```
  npm -v
  ```
  Expect `10.x.x` or `11.x.x`.

**3. Git** — the tool that tracks versions of your files and pushes them to GitHub.

- macOS: it ships with Xcode command line tools. Run `git --version`; if macOS offers to
  install the developer tools, accept.
- Windows: download from https://git-scm.com/download/win and run the installer. Accept
  defaults, but on the "Adjusting your PATH" screen keep the recommended middle option. This
  also installs **Git Bash**, a terminal — use Git Bash for every command in this plan, not
  PowerShell.
- Verify:
  ```
  git --version
  ```
  Expect `git version 2.44.0` or similar.

**4. VS Code** — the text editor. https://code.visualstudio.com

- Verify: it opens, and File → Open Folder works.

**5. Accounts** — free, no card required.

- GitHub: https://github.com/signup — this stores your code and is where you will later edit
  the menu in a browser.
- Netlify: https://app.netlify.com/signup — choose "Sign up with GitHub". This hosts the
  site and gives you the demo URL.

One-time Git identity setup, so commits are attributed to you (use your real email):

```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## 3. Numbered build phases

Ordered so you see a page in a browser inside Phase 1 and have a shareable demo URL by
Phase 5 — realistically day two. Full commands, file contents, checkpoints and failure modes
come **one phase at a time**, when you say "start phase N".

**Phase 1 — Something on screen.** Create the Astro project and run it locally.
*Ends with:* a working project folder and a page at `http://localhost:4321` that updates as
you type. *Checkpoint:* your own text in a browser.

**Phase 2 — Single source of truth.** Create `src/data/restaurant.ts` holding name, address,
phone, email, delivery links and opening hours as structured data; build the header and
footer to read from it, plus a live "Open now / Closed" badge that computes itself from the
hours. *Ends with:* changing one line changes every page. *Checkpoint:* edit the phone number
in the data file, watch it change in the footer of every page at once. This phase is the
direct fix for their core failure — get it right before adding pages.

**Phase 3 — Homepage.** Colour palette, fonts, hero, one-line positioning, open/closed
status, prominent Book a Table button, mobile-first layout. *Checkpoint:* it looks good at
375px wide in your browser's phone preview, not just on your laptop.

**Phase 4 — Menu page.** `src/data/menu.ts` holding every dish, price, course and dietary
marker; the menu page renders from it with jump links per course. Vegetarian / nut /
gluten-free markers as structured fields, never as text you might lose. *Checkpoint:* add a
dish to the data file and it appears in the right course with the right marker.

**Phase 5 — Demo live on a temporary URL.** Push to GitHub, connect Netlify, deploy with
`noindex` so Google never sees it. *Ends with:* the sales asset — a URL you can text to a
restaurant owner. *Checkpoint:* the site loads over HTTPS on your actual phone, on mobile
data with wifi off. **This is the earliest point at which you have something to pitch.**
You can run this phase immediately after Phase 3 if you want the demo sooner.

**Phase 6 — Remaining pages.** About (Chef Pietro Pontone, the family story), Book a Table,
Takeaway & Delivery (collection details plus Deliveroo / Just Eat / Uber Eats), Contact &
Find Us with Google Maps embed and parking, Privacy Policy.

**Phase 7 — Booking.** Embed the chosen system (see below). Until they sign, the demo's
button opens a panel that says "Demo — booking goes live on launch" plus the click-to-call
number. *Checkpoint:* a real booking flow on your phone, using your own test account.

**Phase 8 — SEO and structured data.** Per-page titles and meta descriptions, `Restaurant`
and `Menu` schema.org JSON-LD generated from the same two data files, `openingHoursSpecification`
from the hours data, sitemap, robots.txt, favicon, 404 page. *Checkpoint:* Google's Rich
Results Test passes on the homepage and menu page.

**Phase 9 — Analytics and cookies.** Cloudflare Web Analytics (free, cookieless) or
Plausible (~£7/month). **Legal:** cookieless analytics needs no consent banner under UK
PECR; Google Analytics does, and a banner on a restaurant site costs you bookings. Use
cookieless. A banner is still needed if the booking widget sets cookies — Phase 7 determines
that, which is why this phase comes after it.

**Phase 10 — Images and speed.** Gallery of room and dishes, Astro image optimisation,
proper `alt` text. *Checkpoint:* Lighthouse mobile performance 90+.

**Phase 11 — Pitch pack.** Before/after screenshots, the verified problem list, the retainer
proposal, and the pre-launch checklist in §5.

---

### Booking system — recommendation and real costs

**Recommended: resOS.** Free plan covers 25 bookings/month — enough to demo and enough for
their first weeks. Paid tiers, all with **no per-cover fee and no commission**:

| Plan | Price | Bookings/month |
|---|---|---|
| Free | €0 | 25 |
| Basic | ~€23/mo (~£20) | 350 |
| Plus | ~€43/mo (~£37) | 750 |
| Unlimited | ~€63/mo (~£54) | unlimited |

**Rejected: OpenTable.** $149–$499/month *plus* roughly £2 per cover from its network, plus
a 2% service fee introduced in 2026. For a single neighbourhood restaurant that is hundreds
of pounds a month to rent diners they already had. **Rejected: SevenRooms** (~$499/month,
built for groups). **Rejected: Quandoo** — it is shutting down in December 2026; do not put a
client on it. **UK alternative worth a look: Seatly**, flat £59–£129/month, unlimited
bookings, monthly rolling. Verify every figure on the vendor's own pricing page before you
quote it to the client — these change.

Do not build a reservation system. No-show handling, table-turn logic, GDPR-compliant storage
of customer data and card details for deposits are all liability you do not want on a
retainer.

---

## 4. Content and assets

**Needed from the client (post-signature), by phase:**

| Phase | What | Spec |
|---|---|---|
| 2 | The definitive opening hours | Written confirmation, per day, lunch and evening separately. This is the argument you are being paid to settle — get it from the owner, not the website. |
| 2 | Confirmed phone, address, email | Must match their Google Business Profile character for character. |
| 4 | Current menu with current prices | Their own file or a photo of the printed menu. The 2022 PDFs are stale — assume every price is wrong. |
| 4 | Allergen and dietary information | Legally significant. Get it in writing and add a "please tell us about allergies" line — do not transcribe from an old PDF. |
| 6 | About copy sign-off | Chef Pietro Pontone's story, approved by them. |
| 6 | Delivery platform links | Their actual Deliveroo / Just Eat / Uber Eats URLs. |
| 10 | Photography | Room and dishes, landscape 2400×1600px minimum, JPEG. Their 2018–21 shots are too low-res; budget £300–600 for a half-day local food photographer, or shoot on a recent phone in daylight. |
| 10 | Logo | SVG ideally, otherwise PNG at 1000px+ on transparent background. If all that exists is a low-res web logo, redrawing it is a chargeable extra. |

**Do NOT do these before they sign — every one is a real risk:**

1. **Do not touch their domain or DNS.** Not a lookup you act on, not a transfer, nothing.
   A DNS mistake takes their live site down and the pitch dies with it.
2. **Do not claim, edit or "fix" their Google Business Profile.** Attempting to claim a
   business you do not represent can get your own Google account actioned.
3. **Do not open a booking account in their name**, or use their name, address or phone in a
   vendor signup. Use your own details on a free test account.
4. **Do not publish their photographs on a public URL.** They are the restaurant's (or a
   photographer's) copyright. Build the demo with free-licence stock from Unsplash or Pexels
   and label it "placeholder imagery". A photo of a plate of pasta sells the design just as
   well, and you avoid the one conversation that could end the pitch before it starts.
5. **Do not use their logo in anything public** — a private demo shown to them is fine.
6. **Do not email their customers or scrape anything except their public pages.**
7. **Keep the demo `noindex` and on the netlify.app URL.** A second site with their name and
   hours must never be findable by a real customer.

Menu prices and opening hours are facts and safe to reproduce. The menu's *descriptive
wording* is arguably theirs — fine in a private pitch demo, and it gets replaced with their
signed-off copy at launch either way.

**Get in writing before launch:**

- A signed proposal: scope, price, what the monthly retainer covers, and what "content
  update" means (a price change, yes; a new page, no).
- Written permission to use their name, logo, photographs and menu text.
- The definitive opening hours, signed off by the owner.
- Confirmation they own their domain and who holds the registrar login. If a previous
  developer holds it, that is a problem to solve before launch, not during.
- Who is the data controller for booking data (them) and that they accept the privacy policy
  you supply. **Legal:** under UK GDPR the restaurant is the data controller for customer
  bookings; you are at most a processor. Say so in writing so it is not your liability.
- Permission to switch DNS, with a named date and time.

---

## 5. Launch checklist

**Domain and DNS** (only after signature, and read this before you touch anything — DNS
mistakes are expensive to undo):

- Confirm who controls the registrar. Get the login or get them to make the change with you
  on the phone.
- Point the domain at Netlify per Netlify's own DNS instructions. Change records; do not
  delete records you do not understand, especially `MX` records — deleting those stops their
  email, and `la.casa@btconnect.com` may depend on them.
- Add both `la-casa-weybridge.com` and `www.la-casa-weybridge.com`, pick one as primary,
  redirect the other.
- Wait for propagation (up to 24 hours; usually under one).

**HTTPS:** Netlify issues a free Let's Encrypt certificate automatically. Turn on "Force
HTTPS" so `http://` redirects to `https://` — this is the fix for their current bouncing
between secure and insecure pages. Remove the `noindex` at this point, not before.

**Pre-launch QA:**

- [ ] Renders correctly at 375px, 768px and 1440px wide
- [ ] Tested on a real iPhone and a real Android, on mobile data
- [ ] Click-to-call dials; click-to-email opens the mail app
- [ ] Every link works, including the three delivery platforms and the booking widget
- [ ] Contact/booking submissions actually arrive — send a real test and confirm receipt in
      the restaurant's inbox, including the spam folder
- [ ] Lighthouse mobile: performance 90+, accessibility 95+
- [ ] Favicon appears in the browser tab
- [ ] A deliberately wrong URL shows your styled 404 page with a link home
- [ ] Unique `<title>` and meta description on all seven pages
- [ ] `/sitemap-index.xml` and `/robots.txt` both load
- [ ] Google Rich Results Test passes for `Restaurant` and `Menu` schema
- [ ] Hours in the schema, the footer and the booking widget all agree (they will — they come
      from one file)
- [ ] NAP matches the Google Business Profile exactly
- [ ] Privacy policy live and linked from the footer
- [ ] Old URLs redirect: `/house-menu/` must not 404 for anyone with a bookmark
- [ ] Submit the sitemap in Google Search Console (their account, or one you set up for them
      with permission)

---

## 6. Handover

**What you give them:**

1. The live site.
2. A one-page PDF: how to request a change, what is included in the retainer, response time.
3. Logins they own: domain registrar, booking system, Google Search Console, analytics —
   created in the restaurant's name with the restaurant's email, with you added as a user.
   Never hold their accounts hostage; it is bad practice and it makes the retainer feel like
   a lock-in rather than a service.
4. A one-page "how to read your numbers" note: covers booked online per month, which pages
   people read.

**How content gets edited after launch (you, not them):**

Open `src/data/menu.ts` or `src/data/restaurant.ts` on github.com, click the pencil icon,
change the line, click "Commit changes". Netlify rebuilds and the change is live in about a
minute — every page, the footer, and the structured data Google reads, all at once. Works
from a phone. That is the whole workflow.

**If they later want to edit it themselves:** add Sveltia CMS — a browser admin panel that
edits the same data files. Roughly a day's work, no restructuring. Price it separately.

---

## Appendix — the pitch, in an owner's language

Re-ordered after the 4 Aug evidence check. Lead with money, not technology. Two claims from
the original draft were removed because the source refuted them — never reinstate them.

1. **"Your website tells customers two different closing times."** *(Screenshot still needed
   — get it, this is your opener.)* The booking page says you serve until 11pm on a Friday.
   Every page footer says you close at 10pm. Someone deciding at 9:15pm where to eat reads
   the 10pm and books elsewhere. *(Cost: covers, every week.)*
2. **"You cannot take a booking online. Turquoise can."** Your only route to a table is
   someone ringing during service. People book restaurants at 8pm on a Sunday from the sofa,
   and a phone number is a reason to pick the place that takes bookings on the website.
3. **"Your website has had no maintenance since 2023, and it says so out loud."** *(Verified.)*
   The site itself publishes what it is running: WordPress 6.2.2, from May 2023, and a slider
   plugin from 2018. Every security fix released since has been missed. Worse, those version
   numbers are printed in the page for anyone to read, so nobody has to go looking — a
   list of sites running the old version is trivial to assemble. If it is broken into, the
   usual outcome is not drama: your site quietly starts serving spam links, Google notices
   before you do, and you drop out of local search. *Say "unpatched", never "you have been
   hacked" — you have no evidence of that and you do not want to accuse anyone.*
4. **"Your menu is a PDF from 2022, and the link to it is the insecure kind."** *(Verified.)*
   Your Drinks menu link points at an old-style `http://` address, and the file behind it has
   sat in the same folder since 2022. Two problems in one link: a customer on a phone gets a
   PDF they have to pinch and zoom, showing prices you no longer charge.
5. **"The first thing on your homepage is a notice about a holiday closure."** Not the food,
   not the room, not booking a table.
6. **"Google is being handed almost nothing about you."** *(Corrected — do NOT say "you have
   no sitemap", because they do: WordPress generates one automatically.)* The list Google
   receives is the generic one WordPress makes on its own — four entries, one of which is a
   list of your staff login names rather than anything a diner would search for. There is no
   description written for any page and none of the structured information Google uses to
   show opening hours, prices and menus directly in the search result. Right now you are
   relying entirely on your Google Business listing; the website is contributing nothing.
7. **Photography.** The pictures date from 2018–21 and are too small to fill a modern phone
   screen. Worth raising last, gently — it is the point most likely to be personal.
