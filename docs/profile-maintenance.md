# Profile Maintenance Guide

## Scope

This repository is the GitHub profile landing page for **iamkaifpathaan**.

## Update workflow

1. Update `README.md` content and links.
2. Preserve `assets/banner-dark-animated.svg` as the hero banner source.
3. Keep visual tone dark-first, cyan (`#22D3EE`) / purple (`#A855F7`) accent palette.
4. Let `.github/workflows/snake.yml` regenerate `assets/github-contribution-grid-snake.svg` (light) and `assets/github-contribution-grid-snake-dark.svg` (dark) daily.
5. Let `.github/workflows/stats.yml` regenerate all eight `assets/stats-*.svg` cards every 3 hours.

## GitHub Analytics (self-generated stats, no external hosting)

The public `github-readme-stats.vercel.app` instance is shared by everyone using the project and
regularly returns `503` (rate limit exceeded). Self-hosting it was tried and abandoned — it needs
a personal access token plus an always-on Vercel deployment, and two attempts at that URL still
ended up dead (one behind Vercel's preview-deployment SSO wall, one 404ing). A friend's profile
turned out to be using a different public mirror (`github-readme-stats.shion.dev`, run by one
volunteer) — it works today, but it's the same class of single-point-of-failure that killed the
official instance, so it was deliberately not adopted either. Decision: don't depend on *any*
external stats server, ever again.

Instead, `scripts/generate-stats.mjs` queries the GitHub GraphQL API directly and renders all four
cards as static SVGs, styled to match the banner (dark glass panel, rounded corners, cyan accent
dot, dotted-leader rows). `.github/workflows/stats.yml` runs it **every 3 hours**, on manual
dispatch, and on every push that touches the script, committing the output straight into
`assets/` — same pattern as the contribution snake. It authenticates with the repo's built-in
`GITHUB_TOKEN`, so there is no token to create, no Vercel account, and nothing that can expire or
rate-limit against a shared public instance.

**On "real-time":** these are still static files regenerated on a schedule, not a live query —
that's true of every embeddable README stat card, self-hosted or not (GitHub itself caches
contribution data too). Every card has a small `updated <UTC time>` footer in its bottom-right
corner so that's honest rather than implied. To force an immediate refresh: Actions tab →
*Generate GitHub Stats Cards* → Run workflow.

Output files (light + dark, shown via theme-aware `<picture>` elements like the snake):
- `assets/stats-overview.svg` / `-dark.svg` — public repos, followers, total stars, contributions/
  commits/PRs/issues in the last 12 months. There's no all-time commit count (that needs a
  multi-year GraphQL loop) — "12mo" figures are the accurate, honest scope.
- `assets/stats-top-langs.svg` / `-dark.svg` — top 6 languages by byte share across public,
  non-fork, owned repos, using each language's real GitHub color for its bar.
- `assets/stats-streak.svg` / `-dark.svg` — current and longest contribution streak, computed
  from `contributionCalendar.weeks[].contributionDays[]`. A streak's last day being "today" with
  0 contributions doesn't break it (the day isn't over yet) — see `computeStreaks()`.
- `assets/stats-activity.svg` / `-dark.svg` — a day-by-day area/line chart of the most recent 84
  days of contributions.

Row labels render at their natural monospace width — don't reintroduce a fixed `textLength` /
`lengthAdjust` on label `<text>` elements to force column alignment. It was tried, and it stretches
short labels ("Followers") and squishes long ones ("Pull Requests (12mo)") into visibly distorted
glyph spacing, which is what made the cards look off in the first place. The dotted leader line
already anchors the value column independent of label width, so plain left-aligned text is both
simpler and correct. Card pairs shown side by side in the README (`overview`/`top-langs` at 284px,
`streak`/`activity` at 200px) are also kept at matching heights on purpose — don't let one grow
without adjusting the other, or the two-column grid gets a jagged bottom edge.

To change what any card shows, edit the matching function in `scripts/generate-stats.mjs`
(`overviewCard` / `langCard` / `streakCard` / `activityCard`) — each is covered by an offline unit
test (mocked data, no network) that checks the SVG is well-formed before it's trusted against the
live API.

## Contribution snake

- Workflow: `.github/workflows/snake.yml`, runs daily (`cron: "0 0 * * *"`) and on manual dispatch.
- Produces **two** files: `assets/github-contribution-grid-snake.svg` (light) and
  `assets/github-contribution-grid-snake-dark.svg` (dark), shown via a theme-aware `<picture>` in
  the README.
- The dark variant's first `color_dots` entry (`#2d3343`) is the empty-cell color — it must stay
  visibly lighter than GitHub's dark background (`#0d1117`), or the grid appears broken in dark
  mode.
- Repo Settings → Actions → General → Workflow permissions must be **Read and write** (this is
  the repo's settings, not the account's), or the auto-commit step fails silently.
- After first enabling/editing this workflow, run it once manually (Actions tab → *Generate
  Contribution Snake* → Run workflow) so both SVGs exist before relying on the README render.

## Badges

- Tech-stack and social badges are `shields.io`, `style=for-the-badge`, themed to `#22D3EE` /
  `#A855F7` on a `#0A101F` label background.
- **LinkedIn only renders its logo on brand blue `#0A66C2`** — any custom color silently drops the
  glyph, leaving text only. Keep the LinkedIn badge on brand blue.
- Not every simple-icons slug exists on shields.io (e.g. there's no working icon for "OpenAI" or
  "VS Code" as of this writing) — those badges are intentionally text-only rather than showing a
  wrong/misleading icon. Before adding a new logo badge, verify it actually renders an icon (check
  the file size isn't suspiciously close to a plain no-icon badge) rather than assuming the slug
  works.

## Placeholder checklist

Before publishing major updates, check `README.md` for:
- Project repository URLs.
- LinkedIn URL.
- Portfolio URL (currently `https://portfolio-seven-ebon-79.vercel.app/`, linked from both the
  quick-links row under the hero and the Connect section).
- Contact email.
