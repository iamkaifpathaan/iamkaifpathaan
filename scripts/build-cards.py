"""Builds the animated profile cards and section headers in assets/.

    pip install fonttools uharfbuzz
    python3 scripts/build-cards.py

Outputs (all text outlined to paths, CSS/SMIL animation only, no external
resources, so GitHub's <img> sandbox renders them exactly as designed):
    assets/card-oppo.svg              experience card (1200x470)
    assets/card-royal-compass.svg     live product card (1200x420)
    assets/card-renewal-tracker.svg   live product card (1200x420)
    assets/section-<slug>.svg         section headers, dark
    assets/section-<slug>-light.svg   section headers, light
"""
import math
import os

from svgtext import measure, text

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")

BG = "#0B1020"
PANEL = "#131A2E"
CYAN = "#22D3EE"
PURPLE = "#A855F7"
VIOLET = "#7C3AED"
GREEN = "#10B981"
MINT = "#34D399"
GOLD = "#FBBF24"
AMBER = "#F59E0B"
ROSE = "#FB7185"
WHITE = "#F8FAFC"
MUTED = "#94A3B8"
SLATE = "#334155"

REDUCED = ("@media (prefers-reduced-motion:reduce){*{animation:none!important}"
           # static fallbacks for elements that only make sense mid-animation
           ".n0,.n1,.toast,.scan,.tl-dot,.shine{display:none}.prog{transform:none}}")


def P(s, x, y, fill, key="inter", weight=400, size=16, tracking=0.0, anchor="start", extra=""):
    d, _ = text(s, x, y, key, weight, size, tracking, anchor)
    return f'<path d="{d}" fill="{fill}"{(" " + extra) if extra else ""}/>'


def W(s, key="inter", weight=400, size=16, tracking=0.0):
    return measure(s, key, weight, size, tracking)


def svg(w, h, label, body, style, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{label}">\n<title>{label}</title>\n'
        f"<defs>{defs}</defs>\n<style>{style}{REDUCED}</style>\n{body}\n</svg>\n"
    )


def frame(w, h, glows, uid):
    """Shared glass panel: base, glows, masked grid, border with a travelling light."""
    per = 2 * (w + h - 4 * 28) + 2 * math.pi * 28
    g = "".join(
        f'<radialGradient id="{uid}g{i}" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
        f'gradientTransform="translate({x} {y}) scale({rx} {ry})">'
        f'<stop offset="0" stop-color="{c}" stop-opacity="{o}"/>'
        f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
        for i, (x, y, rx, ry, c, o) in enumerate(glows)
    )
    defs = (
        g
        + f'<pattern id="{uid}grid" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M32 0V32M0 32H32" fill="none" stroke="{WHITE}" stroke-opacity=".05"/></pattern>'
        f'<radialGradient id="{uid}fade" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
        f'gradientTransform="translate({w/2} {h/2}) scale({w*.6} {h*.75})">'
        f'<stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<mask id="{uid}m"><rect width="{w}" height="{h}" fill="url(#{uid}fade)"/></mask>'
        f'<clipPath id="{uid}clip"><rect width="{w}" height="{h}" rx="28"/></clipPath>'
        f'<linearGradient id="{uid}edge" x1="0" y1="0" x2="{w}" y2="{h}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{WHITE}" stop-opacity=".16"/><stop offset=".5" stop-color="{WHITE}" stop-opacity=".05"/>'
        f'<stop offset="1" stop-color="{CYAN}" stop-opacity=".18"/></linearGradient>'
        f'<linearGradient id="{uid}run" x1="0" y1="0" x2="{w}" y2="0" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient>'
    )
    body = (
        f'<g clip-path="url(#{uid}clip)"><rect width="{w}" height="{h}" fill="{BG}"/>'
        + "".join(f'<rect width="{w}" height="{h}" fill="url(#{uid}g{i})"/>' for i in range(len(glows)))
        + f'<rect width="{w}" height="{h}" fill="url(#{uid}grid)" mask="url(#{uid}m)"/></g>'
        f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="27.5" fill="none" stroke="url(#{uid}edge)"/>'
        f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="27.5" fill="none" stroke="url(#{uid}run)" '
        f'stroke-width="1.5" stroke-linecap="round" class="edge-run" style="--per:{per:.0f}px" '
        f'stroke-dasharray="140 {per-140:.0f}"/>'
    )
    style = (
        "@keyframes edgerun{to{stroke-dashoffset:calc(var(--per)*-1)}}"
        ".edge-run{animation:edgerun 9s linear infinite;opacity:.75}"
    )
    return defs, body, style


def pill(x, y, label, color, uid, delay=0.0):
    """Status pill with a pulsing dot. (x, y) = top-left, height 30."""
    tw = W(label, "mono", 500, 12, 0.18)
    w = tw + 50
    return (
        f'<g class="rise" style="animation-delay:{delay}s">'
        f'<rect x="{x}" y="{y}" width="{w:.1f}" height="30" rx="15" fill="{color}" fill-opacity=".10" '
        f'stroke="{color}" stroke-opacity=".35"/>'
        f'<circle cx="{x+18}" cy="{y+15}" r="4" fill="{color}"/>'
        f'<circle cx="{x+18}" cy="{y+15}" r="4" fill="{color}" class="ping"/>'
        + P(label, x + 32, y + 19.5, color, "mono", 500, 12, 0.18)
        + "</g>"
    ), w


COMMON = (
    "@keyframes rise{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:none}}"
    ".rise{animation:rise 1s cubic-bezier(.16,1,.3,1) both}"
    "@keyframes ping{0%{transform:scale(1);opacity:.7}80%,100%{transform:scale(3.2);opacity:0}}"
    ".ping{transform-box:fill-box;transform-origin:center;animation:ping 1.8s cubic-bezier(0,0,.2,1) infinite}"
    "@keyframes shine{0%,55%{transform:translateX(-160px)}85%,100%{transform:translateX(420px)}}"
    ".shine{animation:shine 4.5s cubic-bezier(.4,0,.2,1) infinite}"
    "@keyframes nudge{0%,60%,100%{transform:none}75%{transform:translateX(5px)}}"
    ".nudge{animation:nudge 2.2s cubic-bezier(.4,0,.2,1) infinite}"
)


def cta(x, y, label, uid, grad, arrow="right"):
    """Button with a sweeping shine. (x, y) = top-left, height 48."""
    tw = W(label, "grotesk", 600, 18)
    w = tw + 76
    if arrow == "right":
        ico = f'<path d="M{x+w-40} {y+24}h14m-5-5 5 5-5 5" fill="none" stroke="{BG}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
    else:
        ico = f'<path d="M{x+w-33} {y+16}v14m-5-5 5 5 5-5" fill="none" stroke="{BG}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
    return (
        f'<clipPath id="{uid}btn"><rect x="{x}" y="{y}" width="{w:.1f}" height="48" rx="24"/></clipPath>'
        f'<g class="rise" style="animation-delay:.9s"><g clip-path="url(#{uid}btn)">'
        f'<rect x="{x}" y="{y}" width="{w:.1f}" height="48" fill="url(#{grad})"/>'
        f'<rect x="{x}" y="{y}" width="70" height="48" fill="url(#{uid}shine)" class="shine" transform="skewX(-20)"/></g>'
        + P(label, x + 26, y + 30.5, BG, "grotesk", 600, 18)
        + f'<g class="nudge">{ico}</g></g>'
    ), w


def shine_grad(uid):
    return (
        f'<linearGradient id="{uid}shine" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    )


# ---------------------------------------------------------------- OPPO card
CARD_W = 1200


def text_column(b, u, pill_label, pill_color, kicker, title, title_size, sub, paras, y0=48):
    """Left-hand copy shared by every card: pill + kicker, title, optional sub-line, paragraph."""
    pl, pw_ = pill(56, y0, pill_label, pill_color, u)
    b.append(pl)
    b.append(P(kicker, 56 + pw_ + 16, y0 + 19.5, MUTED, "mono", 500, 12, .22, extra='class="rise" style="animation-delay:.05s"'))
    b.append(P(title, 54, y0 + 102, WHITE, "grotesk", 700, title_size, -0.01, extra='class="rise" style="animation-delay:.12s"'))
    y = y0 + 102
    if sub:
        y += 50
        x = 56
        for i, (s, fill, key, wt, size, tr) in enumerate(sub):
            b.append(P(s, x, y, fill, key, wt, size, tr, extra=f'class="rise" style="animation-delay:{.2+i*.04:.2f}s"'))
            x += W(s, key, wt, size, tr) + 14
    y += 48
    for i, line in enumerate(paras):
        b.append(P(line, 56, y + i * 29, "#A5B4C8", "inter", 400, 19, extra=f'class="rise" style="animation-delay:{.32+i*.05:.2f}s"'))
    return y + (len(paras) - 1) * 29


def oppo_card():
    w, h, u = CARD_W, 470, "o"
    defs, body, style = frame(w, h, [(1010, 230, 420, 330, GREEN, .17), (150, 0, 560, 320, VIOLET, .14)], u)
    defs += (
        f'<linearGradient id="{u}brand" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{MINT}"/>'
        f'<stop offset="1" stop-color="{GREEN}"/></linearGradient>'
        f'<linearGradient id="{u}bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}"/>'
        f'<stop offset="1" stop-color="{MINT}"/></linearGradient>'
        f'<linearGradient id="{u}scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{MINT}" stop-opacity="0"/>'
        f'<stop offset=".85" stop-color="{MINT}" stop-opacity=".22"/><stop offset="1" stop-color="{MINT}" stop-opacity=".9"/></linearGradient>'
        f'<linearGradient id="{u}tl" x1="64" y1="0" x2="780" y2="0" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{CYAN}" stop-opacity=".5"/><stop offset=".6" stop-color="{PURPLE}" stop-opacity=".7"/>'
        f'<stop offset="1" stop-color="{MINT}"/></linearGradient>'
    )
    b = [body]
    ow = W("OPPO", "grotesk", 700, 34, .04)
    y = text_column(
        b, u, "CURRENT ROLE", MINT, "EXPERIENCE  /  NEW CHAPTER", "L1 QA Engineer", 66,
        [("OPPO", f"url(#{u}brand)", "grotesk", 700, 34, .04),
         ("·", MUTED, "inter", 500, 22, 0),
         ("Quality Assurance Engineering", MUTED, "inter", 500, 21, 0)],
        ["Joined OPPO as a Level-1 QA Engineer — executing test plans,",
         "catching defects early and helping every release ship reliable."],
    )
    x, cy = 56, y + 30
    for i, chip in enumerate(["Test Execution", "Bug Reporting", "Regression", "Device Validation"]):
        cw = W(chip, "mono", 500, 14) + 32
        b.append(
            f'<g class="rise" style="animation-delay:{.45+i*.07:.2f}s"><rect x="{x}" y="{cy}" width="{cw:.1f}" height="36" rx="10" '
            f'fill="{WHITE}" fill-opacity=".04" stroke="{WHITE}" stroke-opacity=".12"/>'
            + P(chip, x + 16, cy + 23, "#CBD5E1", "mono", 500, 14) + "</g>"
        )
        x += cw + 10
    # career timeline
    tl_y, x0, x1 = 410, 64, 760
    nodes = [(64, "ELECTRONICS ENGINEER", MUTED), (318, "BUILDER · PABLOCH", MUTED), (560, "QA ENGINEER · OPPO", MINT)]
    b.append(f'<path d="M{x0} {tl_y}H{x1}" stroke="{WHITE}" stroke-opacity=".08" stroke-width="2"/>')
    b.append(f'<path d="M{x0} {tl_y}H{x1}" stroke="url(#{u}tl)" stroke-width="2" stroke-linecap="round" class="tl-draw" style="--L:{x1-x0}"/>')
    b.append(f'<circle r="3.5" fill="#fff" class="tl-dot"><animateMotion dur="3.2s" repeatCount="indefinite" '
             f'path="M{x0} {tl_y}H{x1}" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines=".4 0 .2 1"/></circle>')
    for i, (nx, lab, c) in enumerate(nodes):
        active = i == 2
        b.append(f'<g class="rise" style="animation-delay:{.9+i*.25:.2f}s">')
        if active:
            b.append(f'<circle cx="{nx}" cy="{tl_y}" r="7" fill="{MINT}" class="ping"/>')
        b.append(f'<circle cx="{nx}" cy="{tl_y}" r="{7 if active else 5}" fill="{BG}" stroke="{c}" stroke-width="2"/>')
        if active:
            b.append(f'<circle cx="{nx}" cy="{tl_y}" r="3" fill="{MINT}"/>')
        b.append(P(lab, nx - 8, tl_y + 32, c if active else "#64748B", "mono", 500, 12.5, .14))
        b.append("</g>")
    b.append(P("NOW", x1 + 14, tl_y + 4.5, MINT, "mono", 700, 12, .2, "start", 'class="rise" style="animation-delay:1.6s"'))

    # orbit rings behind the phone
    cx, cy = 1010, 235
    b.append(f'<g fill="none" stroke-linecap="round">'
             f'<circle cx="{cx}" cy="{cy}" r="186" stroke="{MINT}" stroke-opacity=".12" stroke-dasharray="2 10" class="spin" style="transform-origin:{cx}px {cy}px"/>'
             f'<circle cx="{cx}" cy="{cy}" r="218" stroke="{CYAN}" stroke-opacity=".08" stroke-dasharray="60 30 4 30" class="spin-r" style="transform-origin:{cx}px {cy}px"/>'
             f'</g>')
    b.append(f'<g class="spin" style="transform-origin:{cx}px {cy}px"><circle cx="{cx+186}" cy="{cy}" r="4" fill="{MINT}"/>'
             f'<circle cx="{cx-186}" cy="{cy}" r="2.5" fill="{CYAN}" fill-opacity=".7"/></g>')
    # phone (drawn in its own 260x412 coordinate space, placed by translate)
    px, py, pw, ph = 880, 29, 260, 412
    defs += f'<clipPath id="{u}screen"><rect x="14" y="14" width="232" height="384" rx="26"/></clipPath>'
    b.append(f'<g transform="translate({px} {py})"><g class="float">'
             f'<rect width="{pw}" height="{ph}" rx="40" fill="#0E1528" stroke="{SLATE}" stroke-width="2"/>'
             f'<rect x="6" y="6" width="{pw-12}" height="{ph-12}" rx="34" fill="none" stroke="{WHITE}" stroke-opacity=".06"/>'
             f'<rect x="{pw}" y="110" width="3" height="46" rx="1.5" fill="{SLATE}"/>'
             f'<rect x="-3" y="96" width="3" height="30" rx="1.5" fill="{SLATE}"/>'
             f'<circle cx="{pw/2}" cy="26" r="5" fill="#05080F" stroke="{WHITE}" stroke-opacity=".1"/>')
    b.append(f'<g clip-path="url(#{u}screen)">')
    b.append(P("TEST SUITE", 32, 60, MUTED, "mono", 500, 11, .2))
    b.append(P("RUNNING", 228, 60, MINT, "mono", 700, 11, .2, "end", 'class="blink"'))
    b.append(f'<rect x="32" y="72" width="196" height="1" fill="{WHITE}" fill-opacity=".08"/>')
    checks = ["Boot & launch", "UI rendering", "Network & sync", "Camera flow", "Battery & thermal", "Regression pass"]
    T = 9.0
    for i, lab in enumerate(checks):
        ry = 102 + i * 38
        t0 = (0.6 + i * 0.75) / T * 100
        kf = f"k{i}"
        style += (f"@keyframes {kf}s{{0%,{t0-6:.2f}%{{opacity:0}}{t0-5:.2f}%,{t0:.2f}%{{opacity:1}}{t0+.6:.2f}%,100%{{opacity:0}}}}"
                  f"@keyframes {kf}c{{0%,{t0:.2f}%{{stroke-dashoffset:14;opacity:0}}{t0+.3:.2f}%{{opacity:1}}{t0+4:.2f}%,90%{{stroke-dashoffset:0;opacity:1}}96%,100%{{stroke-dashoffset:0;opacity:0}}}}"
                  f"@keyframes {kf}b{{0%,{t0:.2f}%{{fill-opacity:0}}{t0+2:.2f}%,90%{{fill-opacity:.16}}96%,100%{{fill-opacity:0}}}}")
        b.append(f'<rect x="24" y="{ry-18}" width="212" height="32" rx="9" fill="{WHITE}" fill-opacity=".03"/>')
        b.append(P(lab, 60, ry + 3, "#CBD5E1", "inter", 500, 13.5))
        b.append(f'<circle cx="44" cy="{ry-2}" r="8" fill="none" stroke="{SLATE}" stroke-width="1.5"/>')
        b.append(f'<g style="animation:{kf}s {T}s linear infinite both"><circle cx="44" cy="{ry-2}" r="8" fill="none" stroke="{CYAN}" '
                 f'stroke-width="1.8" stroke-dasharray="12 40" stroke-linecap="round" class="spin-fast" style="transform-box:fill-box;transform-origin:center"/></g>')
        b.append(f'<circle cx="44" cy="{ry-2}" r="8" fill="{MINT}" style="animation:{kf}b {T}s linear infinite both"/>')
        b.append(f'<path d="M40 {ry-2}l3 3 5-6" fill="none" stroke="{MINT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
                 f'stroke-dasharray="14" style="animation:{kf}c {T}s linear infinite both"/>')
        b.append(P("PASS", 226, ry + 2, MINT, "mono", 700, 10, .15, "end", f'style="animation:{kf}c {T}s linear infinite both"'))
    b.append(f'<rect x="32" y="342" width="196" height="6" rx="3" fill="{WHITE}" fill-opacity=".08"/>')
    b.append(f'<rect x="32" y="342" width="196" height="6" rx="3" fill="url(#{u}bar)" class="prog"/>')
    b.append(P("ALL CHECKS PASSED", 130, 376, MINT, "mono", 700, 11, .18, "middle", 'class="done"'))
    b.append(f'<rect x="8" y="0" width="244" height="70" fill="url(#{u}scan)" class="scan"/>')
    b.append("</g></g></g>")
    style += (
        COMMON
        + "@keyframes spin{to{transform:rotate(360deg)}}.spin{animation:spin 40s linear infinite}"
        ".spin-r{animation:spin 60s linear infinite reverse}.spin-fast{animation:spin .8s linear infinite}"
        "@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}.float{animation:float 6s ease-in-out infinite}"
        f"@keyframes scan{{0%{{transform:translateY(-10px);opacity:0}}8%{{opacity:1}}62%{{transform:translateY(350px);opacity:1}}66%,100%{{transform:translateY(350px);opacity:0}}}}"
        f".scan{{animation:scan {T}s cubic-bezier(.45,0,.55,1) infinite}}"
        f"@keyframes prog{{0%,6%{{transform:scaleX(0)}}58%,90%{{transform:scaleX(1)}}96%,100%{{transform:scaleX(0)}}}}"
        f".prog{{transform-box:fill-box;transform-origin:left center;animation:prog {T}s cubic-bezier(.4,0,.2,1) infinite}}"
        f"@keyframes done{{0%,60%{{opacity:0;transform:translateY(6px)}}64%,90%{{opacity:1;transform:none}}95%,100%{{opacity:0}}}}"
        f".done{{animation:done {T}s cubic-bezier(.16,1,.3,1) infinite}}"
        "@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}.blink{animation:blink 1.2s ease-in-out infinite}"
        "@keyframes tl{from{stroke-dashoffset:var(--L)}to{stroke-dashoffset:0}}"
        ".tl-draw{stroke-dasharray:var(--L);animation:tl 1.8s cubic-bezier(.65,0,.35,1) .6s both}"
        ".tl-dot{filter:drop-shadow(0 0 6px #fff)}"
    )
    return svg(w, h, "Experience — L1 QA Engineer at OPPO", "\n".join(b), style, defs)


def link_row(b, u, y, url, color, icon, label, grad, arrow):
    """CTA button followed by the plain URL, bottom of the text column."""
    btn, bw = cta(56, y, label, u, grad, arrow)
    b.append(btn)
    ux = 56 + bw + 26
    b.append(f'<g class="rise" style="animation-delay:1s">{icon(ux, y + 24)}'
             + P(url, ux + 22, y + 29.5, color, "mono", 500, 16) + "</g>")


def globe(color):
    return lambda x, y: (f'<circle cx="{x+7}" cy="{y}" r="7" fill="none" stroke="{color}" stroke-width="1.5"/>'
                         f'<path d="M{x} {y}h14M{x+7} {y-7}c-3.5 4-3.5 10 0 14M{x+7} {y-7}c3.5 4 3.5 10 0 14" fill="none" stroke="{color}" stroke-width="1.2"/>')


def phone_icon(color):
    return lambda x, y: (f'<rect x="{x+1}" y="{y-9}" width="12" height="18" rx="3" fill="none" stroke="{color}" stroke-width="1.5"/>'
                         f'<path d="M{x+5} {y+5}h4" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>')


# ------------------------------------------------------- Royal Compass card
def royal_card():
    w, h, u = CARD_W, 420, "r"
    defs, body, style = frame(w, h, [(1040, 210, 360, 300, AMBER, .17), (0, 420, 520, 300, CYAN, .09)], u)
    defs += (
        f'<linearGradient id="{u}gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FDE68A"/>'
        f'<stop offset="1" stop-color="{AMBER}"/></linearGradient>'
        f'<linearGradient id="{u}cta" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FDE68A"/>'
        f'<stop offset="1" stop-color="{AMBER}"/></linearGradient>'
        f'<radialGradient id="{u}face" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1030 212) scale(112)">'
        f'<stop offset="0" stop-color="#1B2440"/><stop offset="1" stop-color="#0E1528"/></radialGradient>'
        + shine_grad(u)
    )
    b = [body]
    text_column(b, u, "LIVE", MINT, "WEBSITE  ·  TRAVEL & TOURS", "Royal Compass Travels", 52, None,
                ["A travel & tours brand website — designed, developed",
                 "and shipped to production on its own domain."])
    link_row(b, u, 324, "royalcompasstravels.com", GOLD, globe(GOLD), "Visit website", f"{u}cta", "right")
    # flight route with plane
    route = "M640 330 C 700 190, 790 120, 880 104"
    b.append(f'<path d="{route}" fill="none" stroke="{WHITE}" stroke-opacity=".10" stroke-width="1.5"/>')
    b.append(f'<path d="{route}" fill="none" stroke="{GOLD}" stroke-opacity=".75" stroke-width="1.5" stroke-dasharray="3 9" stroke-linecap="round" class="march"/>')
    for (x, y, lab, d) in [(640, 330, "DEPART", 0), (880, 104, "ARRIVE", .3)]:
        b.append(f'<g class="rise" style="animation-delay:{.3+d}s"><circle cx="{x}" cy="{y}" r="6" fill="{GOLD}" class="ping" style="animation-delay:{d}s"/>'
                 f'<circle cx="{x}" cy="{y}" r="5.5" fill="{BG}" stroke="{GOLD}" stroke-width="2"/><circle cx="{x}" cy="{y}" r="2" fill="{GOLD}"/>'
                 + P(lab, x, y + 26 if d == 0 else y - 16, "#64748B", "mono", 500, 10, .2, "middle") + "</g>")
    plane = ("M11 0 L-3 -2.2 L-6 -9 L-9 -9 L-7 -2 L-12 -1.4 L-14 -4.5 L-16 -4.5 L-15 0 L-16 4.5 L-14 4.5 L-12 1.4 "
             "L-7 2 L-9 9 L-6 9 L-3 2.2 Z")
    b.append(f'<g><path d="{plane}" fill="{WHITE}" style="filter:drop-shadow(0 0 6px {GOLD})"/>'
             f'<animateMotion dur="5s" repeatCount="indefinite" rotate="auto" path="{route}" keyPoints="0;1;1" keyTimes="0;.8;1" '
             f'calcMode="spline" keySplines=".45 0 .55 1;0 0 1 1"/>'
             f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.06;.74;.8;1" dur="5s" repeatCount="indefinite"/></g>')
    # compass
    cx, cy, r = 1030, 212, 108
    b.append(f'<g class="rise" style="animation-delay:.15s">')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r+24}" fill="none" stroke="{GOLD}" stroke-opacity=".2" stroke-dasharray="1 7" class="spin" style="transform-origin:{cx}px {cy}px"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{u}face)" stroke="url(#{u}gold)" stroke-width="2.5"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r-8}" fill="none" stroke="{WHITE}" stroke-opacity=".08"/>')
    ticks = []
    for i in range(72):
        a = math.radians(i * 5)
        l = 12 if i % 18 == 0 else 7 if i % 2 == 0 else 3.5
        r1, r2 = r - 12, r - 12 - l
        ticks.append(f"M{cx+r1*math.sin(a):.2f} {cy-r1*math.cos(a):.2f}L{cx+r2*math.sin(a):.2f} {cy-r2*math.cos(a):.2f}")
    b.append(f'<path d="{"".join(ticks)}" stroke="{WHITE}" stroke-opacity=".35" stroke-width="1.2"/>')
    for lab, a in [("N", 0), ("E", 90), ("S", 180), ("W", 270)]:
        rr = r - 40
        x = cx + rr * math.sin(math.radians(a))
        y = cy - rr * math.cos(math.radians(a)) + 6
        b.append(P(lab, x, y, GOLD if lab == "N" else MUTED, "grotesk", 700, 17, 0, "middle"))
    b.append(f'<g class="needle" style="transform-origin:{cx}px {cy}px">'
             f'<path d="M{cx} {cy-74} L{cx+10} {cy} L{cx-10} {cy} Z" fill="url(#{u}gold)"/>'
             f'<path d="M{cx} {cy+74} L{cx+10} {cy} L{cx-10} {cy} Z" fill="#475569"/>'
             f'<path d="M{cx} {cy-74} L{cx} {cy+74}" stroke="#000" stroke-opacity=".2"/></g>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{BG}" stroke="{GOLD}" stroke-width="2"/><circle cx="{cx}" cy="{cy}" r="3" fill="{GOLD}"/>')
    b.append("</g>")
    style += (
        COMMON
        + "@keyframes spin{to{transform:rotate(360deg)}}.spin{animation:spin 50s linear infinite}"
        "@keyframes march{to{stroke-dashoffset:-48}}.march{animation:march 1.6s linear infinite}"
        "@keyframes needle{0%{transform:rotate(-40deg)}14%{transform:rotate(28deg)}24%{transform:rotate(-14deg)}"
        "32%{transform:rotate(7deg)}39%{transform:rotate(-3deg)}45%,60%{transform:rotate(0)}"
        "72%{transform:rotate(58deg)}78%{transform:rotate(40deg)}84%,92%{transform:rotate(47deg)}100%{transform:rotate(-40deg)}}"
        ".needle{animation:needle 10s cubic-bezier(.45,0,.55,1) infinite}"
    )
    return svg(w, h, "Royal Compass Travels — live website at royalcompasstravels.com", "\n".join(b), style, defs)


# ----------------------------------------------------- Renewal Tracker card
def renewal_card():
    w, h, u = CARD_W, 420, "t"
    defs, body, style = frame(w, h, [(1000, 180, 380, 300, PURPLE, .19), (720, 240, 260, 220, CYAN, .10)], u)
    defs += (
        f'<linearGradient id="{u}ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}"/>'
        f'<stop offset="1" stop-color="{PURPLE}"/></linearGradient>'
        f'<linearGradient id="{u}cta" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CYAN}"/>'
        f'<stop offset="1" stop-color="#C084FC"/></linearGradient>'
        f'<clipPath id="{u}app"><rect x="860" y="56" width="300" height="308" rx="20"/></clipPath>'
        + shine_grad(u)
    )
    b = [body]
    text_column(b, u, "AVAILABLE", CYAN, "APP  ·  PRODUCTIVITY", "Renewal Tracker", 52, None,
                ["Track every expiry, policy and subscription in one",
                 "place — and get reminded before anything lapses."])
    link_row(b, u, 324, "app.pablochtech.com", CYAN, phone_icon(CYAN), "Download the app", f"{u}cta", "down")
    # countdown ring
    cx, cy, r = 722, 210, 74
    circ = 2 * math.pi * r
    b.append(f'<g class="rise" style="animation-delay:.15s">')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r+18}" fill="none" stroke="{CYAN}" stroke-opacity=".14" stroke-dasharray="2 6" class="spin" style="transform-origin:{cx}px {cy}px"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0E1528" stroke="{WHITE}" stroke-opacity=".07" stroke-width="11"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#{u}ring)" stroke-width="11" stroke-linecap="round" '
             f'stroke-dasharray="{circ:.1f}" class="ring" style="--c:{circ:.1f};transform-origin:{cx}px {cy}px"/>')
    for i, n in enumerate(["30", "12", "03"]):
        b.append(P(n, cx, cy + 13, WHITE, "grotesk", 700, 42, 0, "middle", f'class="n{i}"'))
    b.append(P("DAYS LEFT", cx, cy + 36, MUTED, "mono", 500, 10, .22, "middle"))
    b.append("</g>")
    # app panel
    b.append(f'<g class="rise" style="animation-delay:.25s">')
    b.append(f'<rect x="860" y="56" width="300" height="308" rx="20" fill="#0E1528" fill-opacity=".88" stroke="{WHITE}" stroke-opacity=".10"/>')
    b.append(f'<g clip-path="url(#{u}app)">')
    b.append(P("Upcoming renewals", 882, 94, WHITE, "grotesk", 600, 16))
    bx, by = 1130, 86
    b.append(f'<g class="bell" style="transform-origin:{bx}px {by-9}px"><path d="M{bx-7} {by+4}v-6a7 7 0 0 1 14 0v6l2 3h-18z" fill="none" stroke="{WHITE}" stroke-width="1.6" stroke-linejoin="round"/>'
             f'<path d="M{bx-2.5} {by+10}a2.5 2.5 0 0 0 5 0" fill="none" stroke="{WHITE}" stroke-width="1.6"/></g>'
             f'<circle cx="{bx+8}" cy="{by-9}" r="7" fill="{ROSE}"/>' + P("3", bx + 8, by - 5.5, WHITE, "inter", 700, 10, 0, "middle"))
    b.append(f'<rect x="882" y="112" width="256" height="1" fill="{WHITE}" fill-opacity=".08"/>')
    rows = [("Car Insurance", "12 days", AMBER, .60), ("Domain & Hosting", "3 days", ROSE, .90),
            ("Gym Membership", "28 days", MINT, .25), ("Passport", "6 mo", CYAN, .08)]
    for i, (lab, due, c, frac) in enumerate(rows):
        ry = 146 + i * 54
        b.append(f'<rect x="882" y="{ry-16}" width="28" height="28" rx="8" fill="{c}" fill-opacity=".14"/>'
                 f'<rect x="889" y="{ry-9}" width="14" height="14" rx="3" fill="none" stroke="{c}" stroke-width="1.6"/>'
                 f'<path d="M889 {ry-4}h14" stroke="{c}" stroke-width="1.6"/>')
        b.append(P(lab, 922, ry, "#E2E8F0", "inter", 500, 14))
        b.append(P(due, 1138, ry, c, "mono", 700, 11.5, .05, "end"))
        b.append(f'<rect x="922" y="{ry+10}" width="216" height="4" rx="2" fill="{WHITE}" fill-opacity=".07"/>'
                 f'<rect x="922" y="{ry+10}" width="{216*frac:.1f}" height="4" rx="2" fill="{c}" class="bar" style="animation-delay:{.6+i*.18:.2f}s"/>')
    b.append(f'<g class="toast"><rect x="872" y="68" width="276" height="46" rx="12" fill="#1B2440" stroke="{ROSE}" stroke-opacity=".5"/>'
             f'<circle cx="894" cy="91" r="10" fill="{ROSE}" fill-opacity=".18"/>'
             f'<path d="M894 85v7l4 2" fill="none" stroke="{ROSE}" stroke-width="1.8" stroke-linecap="round"/>'
             + P("Domain & Hosting renews in 3 days", 914, 96, WHITE, "inter", 500, 13) + "</g>")
    b.append("</g></g>")
    T = 9
    style += (
        COMMON
        + "@keyframes spin{to{transform:rotate(360deg)}}.spin{animation:spin 40s linear infinite}"
        f"@keyframes ring{{0%,5%{{stroke-dashoffset:0}}28%,36%{{stroke-dashoffset:calc(var(--c)*.6)}}60%,88%{{stroke-dashoffset:calc(var(--c)*.9)}}100%{{stroke-dashoffset:0}}}}"
        f".ring{{transform:rotate(-90deg);animation:ring {T}s cubic-bezier(.65,0,.35,1) infinite}}"
        f"@keyframes n0{{0%,24%{{opacity:1}}28%,96%{{opacity:0}}100%{{opacity:1}}}}"
        f"@keyframes n1{{0%,24%{{opacity:0}}30%,56%{{opacity:1}}60%,100%{{opacity:0}}}}"
        f"@keyframes n2{{0%,56%{{opacity:0}}62%,90%{{opacity:1}}96%,100%{{opacity:0}}}}"
        f".n0{{animation:n0 {T}s linear infinite}}.n1{{animation:n1 {T}s linear infinite}}.n2{{animation:n2 {T}s linear infinite;fill:{ROSE}}}"
        f"@keyframes toast{{0%,58%{{transform:translateY(-70px);opacity:0}}64%,86%{{transform:none;opacity:1}}92%,100%{{transform:translateY(-70px);opacity:0}}}}"
        f".toast{{animation:toast {T}s cubic-bezier(.16,1,.3,1) infinite}}"
        f"@keyframes bell{{0%,60%,76%,100%{{transform:rotate(0)}}62%{{transform:rotate(18deg)}}64%{{transform:rotate(-16deg)}}66%{{transform:rotate(12deg)}}68%{{transform:rotate(-8deg)}}70%{{transform:rotate(4deg)}}}}"
        f".bell{{animation:bell {T}s ease-in-out infinite}}"
        "@keyframes bar{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        ".bar{transform-box:fill-box;transform-origin:left center;animation:bar 1.4s cubic-bezier(.16,1,.3,1) both}"
    )
    return svg(w, h, "Renewal Tracker — download the app at app.pablochtech.com", "\n".join(b), style, defs)


# ----------------------------------------------------------- section headers
SECTIONS = [
    ("about", "01", "About", "WHO I AM"),
    ("experience", "02", "Experience", "WHERE I WORK"),
    ("live-products", "03", "Live Products", "SHIPPED & IN USE"),
    ("projects", "04", "Featured Projects", "BUILT & BUILDING"),
    ("stack", "05", "Tech Stack", "TOOLS OF THE TRADE"),
    ("analytics", "06", "GitHub Analytics", "AUTO-UPDATED EVERY 3H"),
    ("connect", "07", "Let's Connect", "SAY HELLO"),
]


def section(slug, idx, title, caption, theme):
    w, h = 1200, 96
    dark = theme == "dark"
    tcol = WHITE if dark else "#0F172A"
    mcol = "#64748B"
    acc1 = CYAN if dark else "#0891B2"
    acc2 = PURPLE if dark else VIOLET
    u = "s"
    iw = W(idx, "mono", 700, 16, .1)
    tx = 20 + iw + 48
    tw = W(title, "grotesk", 600, 38, -0.01)
    cw = W(caption, "mono", 500, 13, .24)
    lx1, lx2 = tx + tw + 32, w - 20 - cw - 28
    defs = (
        f'<linearGradient id="{u}l" x1="{lx1}" y1="0" x2="{lx2}" y2="0" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{acc1}" stop-opacity=".9"/><stop offset=".5" stop-color="{acc2}" stop-opacity=".5"/>'
        f'<stop offset="1" stop-color="{acc2}" stop-opacity=".05"/></linearGradient>'
        f'<radialGradient id="{u}glint"><stop offset="0" stop-color="#fff"/><stop offset=".3" stop-color="{acc1}"/>'
        f'<stop offset="1" stop-color="{acc1}" stop-opacity="0"/></radialGradient>'
    )
    b = [
        f'<g class="rise"><rect x="20" y="34" width="{iw+18:.1f}" height="30" rx="8" fill="{acc1}" fill-opacity=".10" stroke="{acc1}" stroke-opacity=".35"/>'
        + P(idx, 29, 55, acc1, "mono", 700, 16, .1) + "</g>",
        f'<rect x="{20+iw+18+6:.1f}" y="48.5" width="10" height="1.5" fill="{acc1}" fill-opacity=".5" class="rise"/>',
        P(title, tx, 62, tcol, "grotesk", 600, 38, -0.01, extra='class="rise" style="animation-delay:.08s"'),
        f'<path d="M{lx1:.1f} 49H{lx2:.1f}" stroke="{tcol}" stroke-opacity=".08" stroke-width="1.5"/>',
        f'<path d="M{lx1:.1f} 49H{lx2:.1f}" stroke="url(#{u}l)" stroke-width="1.5" class="draw" style="--L:{lx2-lx1:.0f}"/>',
        f'<circle cx="{lx1:.1f}" cy="49" r="10" fill="url(#{u}glint)" class="glint" style="--L:{lx2-lx1:.0f}px"/>',
        f'<circle cx="{lx2:.1f}" cy="49" r="3" fill="{acc2}" class="rise" style="animation-delay:.6s"/>',
        P(caption, w - 20, 53.5, mcol, "mono", 500, 13, .24, "end", 'class="rise" style="animation-delay:.2s"'),
    ]
    style = (
        "@keyframes rise{0%{opacity:0;transform:translateY(8px)}100%{opacity:1;transform:none}}"
        ".rise{animation:rise .9s cubic-bezier(.16,1,.3,1) both}"
        "@keyframes draw{from{stroke-dashoffset:var(--L)}to{stroke-dashoffset:0}}"
        ".draw{stroke-dasharray:var(--L);animation:draw 1.6s cubic-bezier(.65,0,.35,1) .2s both}"
        "@keyframes glint{0%{transform:translateX(0);opacity:0}10%{opacity:1}70%{opacity:1}80%,100%{transform:translateX(var(--L));opacity:0}}"
        ".glint{animation:glint 5s cubic-bezier(.65,0,.35,1) 1.8s infinite both}"
    )
    return svg(w, h, f"{idx} — {title}", "\n".join(b), style, defs)


def write(name, content):
    path = os.path.join(ASSETS, name)
    with open(path, "w") as f:
        f.write(content)
    print(f"{name:34s} {len(content)/1024:6.1f} KB")


if __name__ == "__main__":
    write("card-oppo.svg", oppo_card())
    write("card-royal-compass.svg", royal_card())
    write("card-renewal-tracker.svg", renewal_card())
    for slug, idx, title, cap in SECTIONS:
        write(f"section-{slug}.svg", section(slug, idx, title, cap, "dark"))
        write(f"section-{slug}-light.svg", section(slug, idx, title, cap, "light"))
