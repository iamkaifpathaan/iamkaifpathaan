# Profile Maintenance Guide

## Scope

This repository is the GitHub profile landing page for **iamkaifpathaan**.

## Update workflow

1. Update `README.md` content and links.
2. Preserve `assets/banner-dark-animated.svg` as the hero banner source.
3. Keep visual tone dark-first, cyan (`#22D3EE`) / purple (`#A855F7`) accent palette.
4. Let `.github/workflows/snake.yml` regenerate `assets/github-contribution-grid-snake.svg` (light) and `assets/github-contribution-grid-snake-dark.svg` (dark) daily.
5. Let `.github/workflows/stats.yml` regenerate the four `assets/stats-*.svg` cards daily.

## GitHub Analytics (self-generated stats, no external hosting)

The public `github-readme-stats.vercel.app` instance is shared by everyone using the project and
regularly returns `503` (rate limit exceeded). Self-hosting it was tried and abandoned — it needs
a personal access token plus an always-on Vercel deployment, and two attempts at that URL still
ended up dead (one behind Vercel's preview-deployment SSO wall, one 404ing). Decision: don't
depend on it at all, in any form, ever again.

Instead, `scripts/generate-stats.mjs` queries the GitHub GraphQL API directly and renders the
Stats and Top Languages cards as static SVGs, styled to match the banner (dark glass panel,
rounded corners, cyan accent dot, dotted-leader rows). `.github/workflows/stats.yml` runs it daily
and on every push that touches the script, committing the output straight into `assets/` — same
pattern as the contribution snake. It authenticates with the repo's built-in `GITHUB_TOKEN`, so
there is no token to create, no Vercel account, and nothing that can expire or rate-limit against
a shared public instance.

Output files (light + dark, shown via a theme-aware `<picture>` like the snake):
- `assets/stats-overview.svg` / `-dark.svg` — public repos, followers, total stars, contributions/
  commits/PRs/issues in the last 12 months. There's no all-time commit count (that needs a
  multi-year GraphQL loop) — "12mo" figures are the accurate, honest scope.
- `assets/stats-top-langs.svg` / `-dark.svg` — top 6 languages by byte share across public,
  non-fork, owned repos, using each language's real GitHub color for its bar.

To change what it shows, edit `scripts/generate-stats.mjs` (the `overviewCard`/`langCard`
functions) and either wait for the next scheduled run or trigger it manually: Actions tab →
*Generate GitHub Stats Cards* → Run workflow.

`streak-stats.demolab.com` and `github-readme-activity-graph.vercel.app` are unrelated, separate
services and have stayed up on their own — no reason to replace those.

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
- Portfolio URL (currently a "coming soon" badge pointing at the GitHub profile).
- Contact email.
