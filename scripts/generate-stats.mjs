// Generates assets/stats-overview(-dark).svg and assets/stats-top-langs(-dark).svg
// from live GitHub data. Runs inside GitHub Actions using the built-in
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
        contributionCalendar { totalContributions }
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
  return {
    followers: u.followers.totalCount,
    commits: u.contributionsCollection.totalCommitContributions,
    prs: u.contributionsCollection.totalPullRequestContributions,
    issues: u.contributionsCollection.totalIssueContributions,
    contributions: u.contributionsCollection.contributionCalendar.totalContributions,
  };
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

function overviewCard(theme, stats) {
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
  <text x="24" y="${y}" font-family="Consolas,'Fira Code',monospace" font-size="13" fill="${t.label}" textLength="220" lengthAdjust="spacingAndGlyphs">${escapeXml(label)}</text>
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
</svg>`;
}

function langCard(theme, langs) {
  const t = THEMES[theme];
  const width = 495;
  const rowH = 32;
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
  <text x="24" y="${y}" font-family="Consolas,'Fira Code',monospace" font-size="13" fill="${t.label}" textLength="128" lengthAdjust="spacingAndGlyphs">${escapeXml(lang.name)}</text>
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

  const { writeFile, mkdir } = await import("node:fs/promises");
  await mkdir("assets", { recursive: true });

  await writeFile("assets/stats-overview.svg", overviewCard("light", stats));
  await writeFile("assets/stats-overview-dark.svg", overviewCard("dark", stats));
  await writeFile("assets/stats-top-langs.svg", langCard("light", langs));
  await writeFile("assets/stats-top-langs-dark.svg", langCard("dark", langs));

  console.log("Stats:", stats);
  console.log("Top languages:", langs.map((l) => `${l.name} ${l.pct.toFixed(1)}%`).join(", "));
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

export { overviewCard, langCard, topLanguages, escapeXml, chrome };
