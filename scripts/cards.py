"""Genera las tarjetas de estadísticas del README con el mismo diseño del perfil.

Uso:
  GITHUB_TOKEN=... LOGIN=usuario python3 scripts/cards.py   # datos reales (GitHub Actions)
  python3 scripts/cards.py --mock                           # datos de ejemplo para previsualizar
Salida: profile/stats.svg, profile/langs.svg, profile/contrib.svg
"""
import datetime as dt
import json
import os
import random
import sys
import urllib.request
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile")
FONT = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
PALETTE = ["#ff8cc6", "#f472b6", "#db2777", "#c084fc", "#a855f7", "#f9a8d4", "#9d2a6e"]
LEVELS = ["#3d1531", "#5c1a45", "#9d2a6e", "#db2777", "#ff8cc6"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# ---------------------------------------------------------------- datos
def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "readme-cards"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if "errors" in res:
        raise SystemExit(f"GraphQL: {res['errors']}")
    u = res["data"]["user"]
    cc = u["contributionsCollection"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return {
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "contributions": cc["contributionCalendar"]["totalContributions"],
        "prs": u["pullRequests"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "langs": langs,
        "weeks": [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]]
                  for w in cc["contributionCalendar"]["weeks"]],
    }


def mock():
    random.seed(7)
    start = dt.date.today() - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # domingo
    weeks, d = [], start
    while d <= dt.date.today():
        week = []
        for _ in range(7):
            if d <= dt.date.today():
                week.append((d.isoformat(), random.choice([0, 0, 0, 1, 2, 3, 5, 8, 12])))
            d += dt.timedelta(days=1)
        weeks.append(week)
    total = sum(c for w in weeks for _, c in w)
    return {"commits": int(total * .8), "contributions": total, "prs": 14, "repos": 23, "stars": 9,
            "followers": 12, "langs": {"Java": 420000, "JavaScript": 150000, "CSS": 90000, "HTML": 70000,
                                        "TSQL": 20000, "Shell": 4000, "Python": 3000}, "weeks": weeks}


def streaks(weeks):
    days = [c for w in weeks for _, c in w]
    longest = run = 0
    for c in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    i = len(days) - 1
    if i >= 0 and days[i] == 0:  # hoy aún sin contribuciones no rompe la racha
        i -= 1
    current = 0
    while i >= 0 and days[i]:
        current += 1
        i -= 1
    return current, longest


# ---------------------------------------------------------------- piezas comunes
def fmt(n):
    return f"{n:,}".replace(",", ".")


def shell(w, h, title, icon, extra_style="", accent="#f472b6", right=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4a1236"/><stop offset=".6" stop-color="#2a0a20"/><stop offset="1" stop-color="#3b1030"/></linearGradient>
 <radialGradient id="gl" cx=".95" cy="0" r=".7"><stop offset="0" stop-color="{accent}" stop-opacity=".4"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
 <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff8cc6"/><stop offset="1" stop-color="#c084fc"/></linearGradient>
 <style>
  .t{{font:800 26px {FONT};fill:#ffe4f1}}
  .l{{font:600 15px {FONT};fill:#f9a8d4}}
  .v{{font:800 22px {FONT};fill:#ffe4f1}}
  .s{{font:600 12px {FONT};fill:#f9a8d4;opacity:.75}}
  @keyframes pulse{{0%,100%{{opacity:.5}}50%{{opacity:1}}}}
  .glow{{animation:pulse 5s ease-in-out infinite}}
  @keyframes up{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
  .up{{animation:up .7s ease-out both}}
  {extra_style}
 </style>
</defs>
<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="26" fill="url(#bg)" stroke="#f472b6" stroke-opacity=".55" stroke-width="1.5"/>
<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="26" fill="url(#gl)" class="glow"/>
<rect x="40" y="0" width="90" height="4" rx="2" fill="url(#bar)"/>
<g transform="translate(40,34)">
 <rect width="48" height="48" rx="14" fill="#1a0714" fill-opacity=".6" stroke="#f472b6" stroke-opacity=".7"/>
 <g transform="translate(24,24)" fill="none" stroke="#ff8cc6" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{icon}</g>
</g>
<text x="104" y="67" class="t">{escape(title)}</text>
{right}
'''


ICONS = {
    "chart": '<path d="M-12 12V-2M-4 12V-12M4 12V0M12 12V-7"/>',
    "code": '<path d="M-6 -9l-8 9 8 9M6 -9l8 9-8 9"/>',
    "grid": '<rect x="-12" y="-12" width="10" height="10" rx="2"/><rect x="2" y="-12" width="10" height="10" rx="2"/><rect x="-12" y="2" width="10" height="10" rx="2"/><rect x="2" y="2" width="10" height="10" rx="2"/>',
    "cal": '<rect x="-9" y="-8" width="18" height="17" rx="3"/><path d="M-9 -2h18M-4 -11v5M4 -11v5"/>',
    "commit": '<circle r="4.5"/><path d="M-11 0h6.5M4.5 0h6.5"/>',
    "pr": '<circle cx="-5" cy="-7" r="2.6"/><circle cx="-5" cy="7" r="2.6"/><circle cx="6" cy="7" r="2.6"/><path d="M-5 -4.4v8.8M6 4.4V-3a3 3 0 0 0-3-3H0"/>',
    "repo": '<path d="M-8 9V-8a2 2 0 0 1 2-2H8v16H-6a2 2 0 0 0-2 2a2 2 0 0 0 2 2H8"/>',
    "star": '<path d="M0 -10l3 6.3 6.8.9-5 4.7 1.3 6.8L0 5.4-6.1 8.7l1.3-6.8-5-4.7 6.8-.9z"/>',
    "user": '<circle cy="-4" r="4.5"/><path d="M-9 10a9 7 0 0 1 18 0"/>',
}


# ---------------------------------------------------------------- tarjetas
def card_stats(d):
    items = [("cal", "Contribuciones", d["contributions"]), ("commit", "Commits (año)", d["commits"]),
             ("repo", "Repositorios", d["repos"]), ("pr", "Pull Requests", d["prs"]),
             ("star", "Estrellas", d["stars"]), ("user", "Seguidores", d["followers"])]
    body = []
    for i, (ic, label, val) in enumerate(items):
        col, row = i % 2, i // 2
        x, y = 40 + col * 280, 112 + row * 56
        body.append(f'''<g class="up" style="animation-delay:{.1 + i * .08:.2f}s">
 <rect x="{x}" y="{y}" width="260" height="46" rx="14" fill="#1a0714" fill-opacity=".45" stroke="#f472b6" stroke-opacity=".25"/>
 <g transform="translate({x + 24},{y + 23}) scale(.8)" fill="none" stroke="#ff8cc6" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{ICONS[ic]}</g>
 <text x="{x + 46}" y="{y + 28}" class="l">{label}</text>
 <text x="{x + 244}" y="{y + 30}" text-anchor="end" class="v">{fmt(val)}</text>
</g>''')
    return shell(600, 300, "Estadísticas", ICONS["chart"]) + "\n".join(body) + "\n</svg>"


def card_langs(d):
    total = sum(d["langs"].values()) or 1
    top = sorted(d["langs"].items(), key=lambda kv: -kv[1])[:6]
    shown = sum(v for _, v in top) or 1
    style = ".grow{transform-origin:40px 0;animation:grow 1.4s cubic-bezier(.2,.8,.2,1) both}@keyframes grow{from{transform:scaleX(0)}}"
    bar, x = [], 40.0
    for i, (name, v) in enumerate(top):
        w = 520 * v / shown
        bar.append(f'<rect x="{x:.1f}" y="108" width="{max(w - 3, 2):.1f}" height="14" fill="{PALETTE[i]}"/>')
        x += w
    rows = []
    for i, (name, v) in enumerate(top):
        col, row = i % 2, i // 2
        rx, ry = 40 + col * 280, 162 + row * 46
        rows.append(f'''<g class="up" style="animation-delay:{.3 + i * .08:.2f}s">
 <circle cx="{rx + 7}" cy="{ry - 5}" r="7" fill="{PALETTE[i]}"/>
 <text x="{rx + 24}" y="{ry}" class="l" style="fill:#ffe4f1">{escape(name)}</text>
 <text x="{rx + 260}" y="{ry}" text-anchor="end" class="l">{100 * v / total:.1f}%</text>
</g>''')
    clip = '<clipPath id="cb"><rect x="40" y="108" width="520" height="14" rx="7"/></clipPath>'
    return (shell(600, 300, "Lenguajes más usados", ICONS["code"], style)
            + f'<defs>{clip}</defs><rect x="40" y="108" width="520" height="14" rx="7" fill="#1a0714" fill-opacity=".6"/>'
            + f'<g clip-path="url(#cb)"><g class="grow">{"".join(bar)}</g></g>' + "\n".join(rows) + "\n</svg>")


def card_contrib(d):
    weeks = d["weeks"][-53:]
    counts = sorted(c for w in weeks for _, c in w if c)
    def level(c):
        if not c or not counts:
            return 0
        q = [counts[int(len(counts) * p)] for p in (.25, .5, .75)]
        return 1 + sum(c > t for t in q)
    cur, lon = streaks(weeks)
    style = ".c{animation:fade .5s ease-out both}@keyframes fade{from{opacity:0}}"
    legend = "".join(f'<rect x="{1040 + i * 18}" y="56" width="14" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(LEVELS))
    right = f'<text x="1030" y="68" text-anchor="end" class="s">Menos</text>{legend}<text x="1134" y="68" class="s">Más</text>'
    cells, months, last_m = [], [], None
    for wi, w in enumerate(weeks):
        x = 40 + wi * 18
        for date, c in w:
            day = dt.date.fromisoformat(date)
            y = 128 + ((day.weekday() + 1) % 7) * 18
            cells.append(f'<rect class="c" style="animation-delay:{wi * .018:.3f}s" x="{x}" y="{y}" width="14" height="14" rx="3" fill="{LEVELS[level(c)]}"/>')
        m = dt.date.fromisoformat(w[0][0]).month
        if m != last_m and wi < len(weeks) - 2:
            months.append(f'<text x="{x}" y="116" class="s">{MESES[m - 1]}</text>')
            last_m = m
    side = [("Total del año", fmt(d["contributions"])), ("Racha actual", f"{cur} días"), ("Racha más larga", f"{lon} días")]
    panel = "".join(f'''<g class="up" style="animation-delay:{.8 + i * .12:.2f}s"><text x="1030" y="{140 + i * 54}" class="s">{lbl}</text>
<text x="1030" y="{166 + i * 54}" class="v" style="fill:{"#ff8cc6" if i == 1 else "#ffe4f1"}">{val}</text></g>''' for i, (lbl, val) in enumerate(side))
    return (shell(1200, 300, "Contribuciones del último año", ICONS["grid"], style, right=right)
            + "".join(months) + "".join(cells)
            + '<path d="M1010 118V262" stroke="#f472b6" stroke-opacity=".3"/>' + panel + "\n</svg>")


def main():
    data = mock() if "--mock" in sys.argv else fetch(os.environ["LOGIN"], os.environ["GITHUB_TOKEN"])
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("stats", card_stats), ("langs", card_langs), ("contrib", card_contrib)):
        with open(os.path.join(OUT, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(fn(data))
        print("ok", name)


if __name__ == "__main__":
    main()
