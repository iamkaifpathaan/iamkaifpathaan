// Generates assets/stats-{overview,top-langs,streak,activity}(-dark).svg from
// live GitHub data. Runs inside GitHub Actions using the built-in
// GITHUB_TOKEN — no personal access token, no external hosting, ever.
//
// Usage: GH_TOKEN=... GH_LOGIN=iamkaifpathaan node scripts/generate-stats.mjs

const TOKEN = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
const LOGIN = process.env.GH_LOGIN || "iamkaifpathaan";

const PALETTE = {
  cyan: "#22D3EE",
  purple: "#A855F7",
  green: "#10B981",
};

const THEMES = {
  dark: {
    bg: "#0B1020",
    panelFill: "#131A2E",
    panelOpacity: "0.72",
    border: "#22D3EE",
    borderOpacity: "0.16",
    title: "#E2E8F0",
    label: "#94A3B8",
    value: "#F1F5F9",
    track: "#1E293B",
    dot: "#22D3EE",
  },
  light: {
    bg: "#F8FAFC",
    panelFill: "#FFFFFF",
    panelOpacity: "1",
    border: "#0F172A",
    borderOpacity: "0.08",
    title: "#0F172A",
    label: "#475569",
    value: "#0F172A",
    track: "#E2E8F0",
    dot: "#7C3AED",
  },
};

async function ghGraphQL(query, variables) {
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "profile-stats-generator",
    },
    body: JSON.stringify({ query, variables }),
  });
  if (!res.ok) {
    throw new Error(`GraphQL HTTP ${res.status}: ${await res.text()}`);
  }
  const json = await res.json();
  if (json.errors) {
    throw new Error(`GraphQL errors: ${JSON.stringify(json.errors)}`);
  }
  return json.data;
}

const CORE_QUERY = `
  query($login: String!) {
    user(login: $login) {
      followers { totalCount }
      contributionsCollection {
        totalCommitContributions
        totalPullRequestContributions
        totalIssueContributions
        contributionCalendar {
          totalContributions
          weeks {
            contributionDays { date contributionCount }
          }
        }
      }
    }
  }
`;

const REPOS_QUERY = `
  query($login: String!, $after: String) {
    user(login: $login) {
      repositories(
        first: 100
        after: $after
        ownerAffiliations: OWNER
        isFork: false
        privacy: PUBLIC
      ) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes {
          stargazerCount
          languages(first: 10, orderBy: { field: SIZE, direction: DESC }) {
            edges { size node { name color } }
          }
        }
      }
    }
  }
`;

async function fetchCoreStats(login) {
  const data = await ghGraphQL(CORE_QUERY, { login });
  const u = data.user;
  const days = u.contributionsCollection.contributionCalendar.weeks.flatMap((w) =>
    w.contributionDays.map((d) => ({ date: d.date, count: d.contributionCount }))
  );
  return {
    followers: u.followers.totalCount,
    commits: u.contributionsCollection.totalCommitContributions,
    prs: u.contributionsCollection.totalPullRequestContributions,
    issues: u.contributionsCollection.totalIssueContributions,
    contributions: u.contributionsCollection.contributionCalendar.totalContributions,
    days,
  };
}

// days: chronologically ascending [{date:'YYYY-MM-DD', count:Number}, ...]
function computeStreaks(days) {
  let longestLen = 0;
  let longestStart = null;
  let longestEnd = null;
  let run = 0;
  let runStart = null;

  for (const d of days) {
    if (d.count > 0) {
      if (run === 0) runStart = d.date;
      run++;
      if (run > longestLen) {
        longestLen = run;
        longestStart = runStart;
        longestEnd = d.date;
      }
    } else {
      run = 0;
    }
  }

  // Current streak: today (last entry) not having contributions yet doesn't
  // break it, since the day isn't over — only look backward from there.
  let i = days.length - 1;
  if (days[i] && days[i].count === 0) i--;
  const endIdx = i;
  let currentLen = 0;
  while (i >= 0 && days[i].count > 0) {
    currentLen++;
    i--;
  }

  return {
    current: {
      length: currentLen,
      start: currentLen > 0 ? days[i + 1].date : null,
      end: currentLen > 0 ? days[endIdx].date : null,
    },
    longest: { length: longestLen, start: longestStart, end: longestEnd },
  };
}

function formatShortDate(dateStr) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

function formatLongDate(dateStr) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
}

function formatTimestamp(now) {
  return `${now.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

async function fetchReposAggregate(login) {
  let after = null;
  let totalRepos = 0;
  let totalStars = 0;
  const languages = new Map(); // name -> { bytes, color }

  for (let page = 0; page < 10; page++) {
    const data = await ghGraphQL(REPOS_QUERY, { login, after });
    const repos = data.user.repositories;
    totalRepos = repos.totalCount;
    for (const repo of repos.nodes) {
      totalStars += repo.stargazerCount;
      for (const edge of repo.languages.edges) {
        const name = edge.node.name;
        const prev = languages.get(name) || { bytes: 0, color: edge.node.color || "#8b949e" };
        prev.bytes += edge.size;
        languages.set(name, prev);
      }
    }
    if (!repos.pageInfo.hasNextPage) break;
    after = repos.pageInfo.endCursor;
  }

  return { totalRepos, totalStars, languages };
}

function topLanguages(languages, limit = 6) {
  const totalBytes = [...languages.values()].reduce((sum, l) => sum + l.bytes, 0);
  return [...languages.entries()]
    .sort((a, b) => b[1].bytes - a[1].bytes)
    .slice(0, limit)
    .map(([name, l]) => ({
      name,
      color: l.color,
      pct: totalBytes ? (l.bytes / totalBytes) * 100 : 0,
    }));
}

function escapeXml(str) {
  return String(str).replace(/[<>&"']/g, (c) => ({
    "<": "&lt;",
    ">": "&gt;",
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
  }[c]));
}

function chrome(theme, width, height, title) {
  const t = THEMES[theme];
  return `
<rect width="${width}" height="${height}" rx="18" fill="${t.bg}"/>
<rect x="1" y="1" width="${width - 2}" height="${height - 2}" rx="17" fill="${t.panelFill}" fill-opacity="${t.panelOpacity}"/>
<rect x="1.5" y="1.5" width="${width - 3}" height="${height - 3}" rx="16.5" fill="none" stroke="${t.border}" stroke-opacity="${t.borderOpacity}"/>
<g fill="${t.dot}" fill-opacity=".28">
  <rect x="${width - 34}" y="16" width="5" height="5" rx="1"/>
  <rect x="${width - 22}" y="16" width="5" height="5" rx="1"/>
</g>
<rect x="24" y="14" width="5" height="5" rx="1" fill="${PALETTE.cyan}"/>
<text x="36" y="23" font-family="Consolas,'Fira Code',monospace" font-size="13" font-weight="700" fill="${t.title}">${escapeXml(title)}</text>
<rect x="24" y="34" width="${width - 48}" height="1" fill="${t.border}" fill-opacity="${t.borderOpacity}"/>`;
}

function timestampFooter(theme, width, height, now) {
  const t = THEMES[theme];
  return `<text x="${width - 16}" y="${height - 10}" text-anchor="end" font-family="Consolas,'Fira Code',monospace" font-size="9" fill="${t.label}" fill-opacity=".55">updated ${escapeXml(formatTimestamp(now))}</text>`;
}

function overviewCard(theme, stats, now = new Date()) {
  const t = THEMES[theme];
  const width = 495;
  const rows = [
    ["Public Repos", stats.totalRepos],
    ["Followers", stats.followers],
    ["Total Stars", stats.totalStars],
    ["Contributions (12mo)", stats.contributions],
    ["Commits (12mo)", stats.commits],
    ["Pull Requests (12mo)", stats.prs],
    ["Issues (12mo)", stats.issues],
  ];
  const rowH = 30;
  const top = 56;
  const height = top + rows.length * rowH + 18;

  const rowsSvg = rows
    .map(([label, value], i) => {
      const y = top + i * rowH;
      const delay = (0.08 * i).toFixed(2);
      return `
<g opacity="0" class="row-fade" style="animation-delay:${delay}s">
  <text x="24" y="${y}" font-family="Consolas,'Fira Code',monospace" font-size="13" fill="${t.label}">${escapeXml(label)}</text>
  <line x1="252" y1="${y - 4}" x2="${width - 96}" y2="${y - 4}" stroke="${t.track}" stroke-width="1" stroke-dasharray="1,4"/>
  <text x="${width - 24}" y="${y}" text-anchor="end" font-family="Consolas,'Fira Code',monospace" font-size="13" font-weight="700" fill="${t.value}">${escapeXml(value.toLocaleString())}</text>
</g>`;
    })
    .join("");

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="GitHub stats overview for ${LOGIN}">
<style>
.row-fade { animation: fadeIn .6s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
${chrome(theme, width, height, "stats.sh --overview")}
${rowsSvg}
${timestampFooter(theme, width, height, now)}
</svg>`;
}

function langCard(theme, langs, now = new Date()) {
  const t = THEMES[theme];
  const width = 495;
  // Matches overviewCard's 7-row height (56 + 7*30 + 18 = 284) so the two
  // cards line up edge-to-edge when shown side by side in the README.
  const rowH = 35;
  const top = 56;
  const height = top + langs.length * rowH + 18;
  const barX = 160;
  const barW = 260;
  const barTrackY = 8;
  const barH = 7;

  const rowsSvg = langs
    .map((lang, i) => {
      const y = top + i * rowH;
      const delay = (0.08 * i).toFixed(2);
      const fillW = (barW * lang.pct) / 100;
      return `
<g opacity="0" class="row-fade" style="animation-delay:${delay}s">
  <text x="24" y="${y}" font-family="Consolas,'Fira Code',monospace" font-size="13" fill="${t.label}">${escapeXml(lang.name)}</text>
  <rect x="${barX}" y="${y - barTrackY}" width="${barW}" height="${barH}" rx="3.5" fill="${t.track}"/>
  <rect x="${barX}" y="${y - barTrackY}" width="0" height="${barH}" rx="3.5" fill="${lang.color}">
    <animate attributeName="width" from="0" to="${fillW.toFixed(2)}" dur=".8s" begin="${delay}s" fill="freeze"/>
  </rect>
  <text x="${width - 24}" y="${y}" text-anchor="end" font-family="Consolas,'Fira Code',monospace" font-size="13" font-weight="700" fill="${t.value}">${lang.pct.toFixed(1)}%</text>
</g>`;
    })
    .join("");

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Top languages for ${LOGIN}">
<style>
.row-fade { animation: fadeIn .6s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
${chrome(theme, width, height, "langs.sh --top")}
${rowsSvg}
${timestampFooter(theme, width, height, now)}
</svg>`;
}

function streakCard(theme, streaks, now = new Date()) {
  const t = THEMES[theme];
  const width = 495;
  // Matches activityCard's height so the two cards line up edge-to-edge
  // when shown side by side in the README.
  const height = 200;
  const dividerX = 247.5;
  const leftCenter = 135;
  const rightCenter = 360;

  const tile = (cx, color, length, rangeLabel, label, delay) => `
<g opacity="0" class="row-fade" style="animation-delay:${delay}s" text-anchor="middle">
  <text x="${cx}" y="118" font-family="Consolas,'Fira Code',monospace" font-size="42" font-weight="700" fill="${color}">${length}</text>
  <text x="${cx}" y="140" font-family="Consolas,'Fira Code',monospace" font-size="12" font-weight="700" letter-spacing="1" fill="${t.value}">${escapeXml(label)}</text>
  <text x="${cx}" y="158" font-family="Consolas,'Fira Code',monospace" font-size="11" fill="${t.label}">${escapeXml(rangeLabel)}</text>
</g>`;

  const currentRange = streaks.current.length > 0
    ? `${formatLongDate(streaks.current.start)} – Present`
    : "No active streak";
  const longestRange = streaks.longest.length > 0
    ? `${formatShortDate(streaks.longest.start)} – ${formatShortDate(streaks.longest.end)}`
    : "—";

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Contribution streaks for ${LOGIN}">
<style>
.row-fade { animation: fadeIn .6s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
${chrome(theme, width, height, "streak.sh --status")}
${tile(leftCenter, PALETTE.purple, streaks.current.length, currentRange, "CURRENT STREAK", "0.00")}
<line x1="${dividerX}" y1="56" x2="${dividerX}" y2="${height - 34}" stroke="${t.border}" stroke-opacity="${t.borderOpacity}"/>
${tile(rightCenter, PALETTE.cyan, streaks.longest.length, longestRange, "LONGEST STREAK", "0.08")}
${timestampFooter(theme, width, height, now)}
</svg>`;
}

function activityCard(theme, days, now = new Date()) {
  const t = THEMES[theme];
  const width = 495;
  const height = 200;
  const chartLeft = 44;
  const chartRight = width - 24;
  const chartTop = 56;
  const chartBottom = height - 34;
  const chartW = chartRight - chartLeft;
  const chartH = chartBottom - chartTop;

  const window = days.slice(-84);
  const max = Math.max(1, ...window.map((d) => d.count));
  const n = Math.max(1, window.length - 1);

  const points = window.map((d, i) => {
    const x = chartLeft + (chartW * i) / n;
    const y = chartBottom - (d.count / max) * chartH;
    return [x, y];
  });

  const linePath = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${chartRight.toFixed(1)},${chartBottom} L${chartLeft.toFixed(1)},${chartBottom} Z`;

  const gridLines = [0, 0.5, 1]
    .map((f) => {
      const y = chartBottom - f * chartH;
      const val = Math.round(max * f);
      return `
<line x1="${chartLeft}" y1="${y.toFixed(1)}" x2="${chartRight}" y2="${y.toFixed(1)}" stroke="${t.track}" stroke-width="1" stroke-dasharray="1,4"/>
<text x="${chartLeft - 8}" y="${(y + 3).toFixed(1)}" text-anchor="end" font-family="Consolas,'Fira Code',monospace" font-size="9" fill="${t.label}">${val}</text>`;
    })
    .join("");

  const rangeLabel = window.length
    ? `${formatShortDate(window[0].date)} – ${formatShortDate(window[window.length - 1].date)}`
    : "";

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Daily contribution activity for ${LOGIN}">
<defs>
  <linearGradient id="areaFill-${theme}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="${PALETTE.cyan}" stop-opacity=".35"/>
    <stop offset="100%" stop-color="${PALETTE.purple}" stop-opacity="0"/>
  </linearGradient>
</defs>
<style>
.row-fade { animation: fadeIn .6s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
${chrome(theme, width, height, "activity.sh --graph")}
<g opacity="0" class="row-fade" style="animation-delay:0.05s">
${gridLines}
<path d="${areaPath}" fill="url(#areaFill-${theme})" stroke="none"/>
<path d="${linePath}" fill="none" stroke="${PALETTE.cyan}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
<text x="${chartLeft}" y="${height - 16}" font-family="Consolas,'Fira Code',monospace" font-size="10" fill="${t.label}">${escapeXml(rangeLabel)}</text>
</g>
${timestampFooter(theme, width, height, now)}
</svg>`;
}

async function main() {
  if (!TOKEN) {
    console.error("Missing GH_TOKEN / GITHUB_TOKEN in environment.");
    process.exit(1);
  }

  const [core, repoAgg] = await Promise.all([
    fetchCoreStats(LOGIN),
    fetchReposAggregate(LOGIN),
  ]);

  const stats = {
    totalRepos: repoAgg.totalRepos,
    totalStars: repoAgg.totalStars,
    followers: core.followers,
    contributions: core.contributions,
    commits: core.commits,
    prs: core.prs,
    issues: core.issues,
  };
  const langs = topLanguages(repoAgg.languages, 6);
  const streaks = computeStreaks(core.days);
  const now = new Date();

  const { writeFile, mkdir } = await import("node:fs/promises");
  await mkdir("assets", { recursive: true });

  await writeFile("assets/stats-overview.svg", overviewCard("light", stats, now));
  await writeFile("assets/stats-overview-dark.svg", overviewCard("dark", stats, now));
  await writeFile("assets/stats-top-langs.svg", langCard("light", langs, now));
  await writeFile("assets/stats-top-langs-dark.svg", langCard("dark", langs, now));
  await writeFile("assets/stats-streak.svg", streakCard("light", streaks, now));
  await writeFile("assets/stats-streak-dark.svg", streakCard("dark", streaks, now));
  await writeFile("assets/stats-activity.svg", activityCard("light", core.days, now));
  await writeFile("assets/stats-activity-dark.svg", activityCard("dark", core.days, now));

  console.log("Stats:", stats);
  console.log("Top languages:", langs.map((l) => `${l.name} ${l.pct.toFixed(1)}%`).join(", "));
  console.log("Streaks:", streaks);
}

// Only auto-run when executed directly (`node generate-stats.mjs`), so the
// pure render functions above can be imported and unit-tested without
// triggering a live network call.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}

export {
  overviewCard,
  langCard,
  streakCard,
  activityCard,
  topLanguages,
  computeStreaks,
  formatShortDate,
  formatLongDate,
  escapeXml,
  chrome,
};
