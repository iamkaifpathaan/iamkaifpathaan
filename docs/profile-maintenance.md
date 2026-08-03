# Profile Maintenance Guide

## Scope

This repository is the GitHub profile landing page for **iamkaifpathaan**.

## Update workflow

1. Update `README.md` content and links.
2. Preserve `assets/banner-dark-animated.svg` as the hero banner source.
3. Keep visual tone dark-first, cyan (`#22D3EE`) / purple (`#A855F7`) accent palette.
4. Let `.github/workflows/snake.yml` regenerate `assets/github-contribution-grid-snake.svg` (light) and `assets/github-contribution-grid-snake-dark.svg` (dark) daily.

## Fixing the GitHub Analytics section (self-hosting stats)

The public `github-readme-stats.vercel.app` instance is shared by everyone using the project and
regularly returns `503` (rate limit exceeded) — that's the "dead URL" behind the Stats and Top
Languages cards. `streak-stats.demolab.com` and `github-readme-activity-graph.vercel.app` are
separate services and stay up on their own.

Fix it once, ~20 minutes, no cost:

1. **Create a GitHub token** — `github.com/settings/tokens` → Tokens (classic) → Generate new
   token (classic) → scope `repo` → No expiration. Copy it immediately; never paste it into a
   chat, a public repo, or a website.
2. **Fork** [`anuraghazra/github-readme-stats`](https://github.com/anuraghazra/github-readme-stats).
3. **Deploy on Vercel** — `vercel.com` → Sign up with GitHub → Hobby (free) → Add New Project →
   import the fork → leave build settings alone.
4. **Add an environment variable**: name `PAT_1`, value = the token from step 1. Deploy.
5. **Copy your instance URL** (`your-instance.vercel.app`) and replace every
   `YOUR-STATS-INSTANCE` placeholder in `README.md`'s GitHub Analytics section with it.
6. Verify: `https://your-instance.vercel.app/api?username=iamkaifpathaan&show_icons=true` should
   render a card, not an error.

`hide_rank=true` is set deliberately — the rank is stars/follower-weighted and misrepresents a
newer account, so it's hidden rather than shown misleadingly.

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
- `YOUR-STATS-INSTANCE` — must be replaced after self-hosting (see above).
- Project repository URLs.
- LinkedIn URL.
- Portfolio URL (currently a "coming soon" badge pointing at the GitHub profile).
- Contact email.
