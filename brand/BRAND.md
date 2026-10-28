# Luvita brand and copy rules

The public brand, attribution and copy rules for every Luvita surface: the
websites, app store listings, READMEs and anything else a stranger can read.
Agents working on a Luvita site read this file live from this repository
before they write copy.

This file is public. It holds only rules that are safe to publish. Each site's
`CLAUDE.md` and `brand-rules.json` hold its own site-specific rules and win on
anything they cover; a site's `brand-check` run is the enforced floor, and this
file is the reason behind it.

## The company

- **Luvita** is a software product company. It builds products and keeps them
  running. It does not sell services, consultancy or team augmentation, and no
  surface should suggest it does.
- The legal entity is **Luvita Teknoloji Enerji Yazılım Sanayi ve Ticaret
  Limited Şirketi**, Türkiye. It is the only copyright holder for every product
  below: never a brand, never a person.
- Short form of the name, for product surfaces: **Luvita Teknoloji Ltd. Şti.**
- The full registered name contains "Enerji". It is legal identity, not copy:
  it appears only in legal-identity blocks (footer legal line, identity page,
  Organization JSON-LD `legalName`), never in a headline, a lead, body copy or
  a meta description.
- **luvita.tr** is the company's identity page and the target of every
  attribution link.

## Brands and products

| Name | What it is | Public surface |
| --- | --- | --- |
| **Luvita** | The software product company | luvita.tr |
| **CosmoCrew** | Luvita's consumer-apps brand | cosmocrew.dev |
| **SliceFocus** | CosmoCrew app: 24-hour radial planner with a focus timer | slicefocus.app, App Store |
| **LexiPower** | CosmoCrew app: vocabulary notebook with spaced repetition | lexipower.app, App Store |
| **With Handlebars** | CosmoCrew app: guitar chord and scale fretboard explorer | withhandlebars.com |
| **Umay** | Luvita product, no intermediate brand | umayconnect.org |
| **Nesili** | Luvita product, no intermediate brand | nesili.com |
| **Luvi Engine** | Luvita product, no intermediate brand | none yet |
| **Luvita Enerji** | A separate consumer solar business of the same company | its own site |

Public product names, exactly as written:

- **LexiPower**, never "WordPower" (an internal codename).
- **Umay**, never "Yaren" (a former name).
- **Nesili**: the name is not a registered trademark. Never write ® next to
  it, and add ™ only where the founder asks for it.
- **CosmoCrew** in prose. `AnunnakiCosmoCrew` is the GitHub organisation name,
  not a brand to present.

## Attribution (luvita-docs ADR 0001)

Every public software product surface carries a one-line attribution that
names the company and links to `https://luvita.tr/`, readable without leaving
the page. The footer is the expected place. A chain through another site
(product site → cosmocrew.dev → luvita.tr) does not count: every surface names
Luvita directly.

Copy these strings verbatim. In all four, `Luvita Teknoloji Ltd. Şti.` is the
link text and `https://luvita.tr/` is the target. The year follows the current
year the way each site already handles it.

CosmoCrew surfaces (the apps and cosmocrew.dev):

- EN: `© 2026 CosmoCrew — a brand of Luvita Teknoloji Ltd. Şti.`
- TR: `© 2026 CosmoCrew — Luvita Teknoloji Ltd. Şti. markasıdır.`

Direct Luvita products (Umay, Nesili, Luvi Engine, and any future product with
no intermediate brand):

- EN: `A Luvita product — Luvita Teknoloji Ltd. Şti.`
- TR: `Bir Luvita ürünü — Luvita Teknoloji Ltd. Şti.`

Rules around the line:

- `© CosmoCrew` leads on CosmoCrew surfaces and is never replaced by
  `© Luvita`. CosmoCrew is a deliberate brand; the clause after it names the
  legal holder.
- The holder is never a person. A line such as `© 2026 <a name> · <app>` is a
  defect.
- A new public product surface ships with the line on day one. Shipping
  without it is a defect, not a follow-up.
- **Exception, Luvita Enerji:** the solar site names the company
  ("Bir Luvita Teknoloji kuruluşudur.") but does not link to luvita.tr. Software
  and solar stay apart in both directions.

## Software and solar stay apart

- luvita.tr carries no solar content and never names the solar brand. The full
  legal name (which contains "Enerji") may appear there only in legal-identity
  blocks.
- The solar site may say it is a Luvita Teknoloji company and never links to
  luvita.tr.
- luvita.tr may describe Luvi Engine as software. It never implies that Luvita
  does solar installations.

## Address and location

- Never publish a street address on any of our own surfaces: sites, repos,
  READMEs, copy, screenshots.
- Where a location is shown, it is city-level: "Bodrum, Muğla / Türkiye".
- **luvita.tr shows no city at all**: not in the hero, not in visible copy, not
  in a meta or social description. The city survives only in its JSON-LD
  address block.
- No city in a hero anywhere. The company may move.
- Registry numbers (MERSİS, VKN) belong on luvita.tr's identity page, not on
  product sites.

## Claims

### Nesili: the claim floor

Never state or imply, in any language, on any surface (copy, README, docs,
code comment, commit, issue or PR) that using Nesili means **no personal data
crosses the border**, or that it **removes, waives or exempts the customer's
KVKK Article 9 obligations**. Quoting that claim to deny it counts too; link to
this rule instead of restating it.

Write instead, in substance: Nesili keeps raw identifiers in Türkiye (on the
desktop product: on the user's own computer) and materially reduces the
re-identification, disclosure and breach risk in what does cross; the
customer's own Article 9 basis is still required, and Nesili makes meeting it
easier, not unnecessary.

### No unmeasured numbers

- **Nesili:** no timing, throughput or latency figure on any surface, README,
  screenshot alt text, issue or PR until it has been measured on the real
  system. Show a spinner, never a stopwatch.
- **Umay:** marketing pages name no speech or model provider. Turkish quality
  is measured, not asserted.
- In general: a number in public copy is one we have measured and can show.

## Voice

### Luvita

- Founder-led and craftsman: the product is engineered end to end by the same
  hands.
- State what things are and do. No definition by negation ("we are not a
  …", "no X, no Y" as a positioning line).
- Hero line, as shipped: "Ürün geliştiriyoruz, yayında tutuyoruz." / "We build
  products and keep them running."

### CosmoCrew

- Feel indie and ambitious without saying it. Avoid "small", "indie",
  "humble", "modest".
- Don't lean on "studio"; prefer "the crew" or "we".
- Shipped line: "Calm, capable software, crafted to last."

### Headlines

- An h1 needs a verb.
- A definition ("X is a Y") goes at lead size, not in the h1.

### Turkish words we don't use

- "teslimat" (reads as cargo delivery)
- "teslim tarihini aşan"
- "ekip kiralamıyoruz"
- "ölümsüz"
- "kendini geliştiren"

## Where things are listed

- luvita.tr lists and links every product and brand the company owns.
- cosmocrew.dev lists only CosmoCrew apps. Umay, Nesili and Luvi Engine are
  listed on luvita.tr, not there.

## Keeping this file current

The private company reference is the source; this file is its public half.
When a brand or copy rule changes there, this file changes in the same week,
and so does any `brand-rules.json` that enforces it. If this file and a site's
`CLAUDE.md` disagree, the site's `CLAUDE.md` wins for that site; raise the
mismatch on an issue in this repository.
