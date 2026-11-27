#!/usr/bin/env python3
"""Collect current NBA week scoreboard and final box scores into data/nba_week.json."""
from __future__ import annotations
import json, os, sys, time
from datetime import datetime, timedelta, date
from pathlib import Path
from zoneinfo import ZoneInfo
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "nba_week.json"
BASE = "https://cdn.nba.com/static/json/liveData"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ALEX-NBA-Collector/2.3; +https://github.com)",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get_json(url: str):
    last = None
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=25)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Richiesta fallita {url}: {last}")


def season_for(d: str) -> str:
    y, m = int(d[:4]), int(d[5:7])
    return f"{y}-{str(y+1)[-2:]}" if m >= 10 else f"{y-1}-{str(y)[-2:]}"


def team_name(t: dict) -> str:
    return " ".join(x for x in (t.get("teamCity"), t.get("teamName")) if x) or t.get("teamTricode", "Squadra")


def minutes(v):
    if not v:
        return None
    s = str(v)
    if s.startswith("PT"):
        import re
        m = re.match(r"PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", s)
        if m:
            return round(int(m.group(1) or 0) + float(m.group(2) or 0) / 60, 2)
    if ":" in s:
        try:
            a, b = s.split(":", 1)
            return round(int(a) + int(b[:2]) / 60, 2)
        except Exception:
            return None
    try:
        return float(s)
    except Exception:
        return None


def week_dates():
    today = datetime.now(ZoneInfo("America/New_York")).date()
    monday = today - timedelta(days=today.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def main():
    dates = week_dates()
    old = {"schema": 1, "updatedAt": None, "weekStart": dates[0].isoformat(), "weekEnd": dates[-1].isoformat(), "games": [], "playerStats": []}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            print("Archivio precedente illeggibile: non verrà sovrascritto.", file=sys.stderr)
            raise
    games = {str(x.get("id")): x for x in old.get("games", []) if x.get("id")}
    stats = {str(x.get("id")): x for x in old.get("playerStats", []) if x.get("id")}
    found_count = 0
    day_errors = []
    for day in dates:
        ds = day.strftime("%Y%m%d")
        try:
            payload = get_json(f"{BASE}/scoreboard/scoreboard_{ds}.json")
            day_games = payload.get("scoreboard", {}).get("games", [])
            for raw in day_games:
                gid = str(raw.get("gameId") or "")
                if not gid:
                    continue
                found_count += 1
                h, a = raw.get("homeTeam", {}), raw.get("awayTeam", {})
                status = int(raw.get("gameStatus") or 0)
                hs, aws = h.get("score"), a.get("score")
                final = status == 3 and hs is not None and aws is not None
                game_date = str(raw.get("gameEt") or raw.get("gameDate") or day.isoformat())[:10]
                prev = games.get(gid, {})
                games[gid] = {
                    **prev, "id": gid, "date": game_date, "season": season_for(game_date),
                    "home": team_name(h), "away": team_name(a),
                    "homeScore": int(hs) if final else None, "awayScore": int(aws) if final else None,
                    "score": f"{hs}-{aws}" if final else "",
                    "winner": ("H" if int(hs) > int(aws) else "A" if int(hs) < int(aws) else "T") if final else "",
                    "total": int(hs) + int(aws) if final else None,
                    "gameStatus": status, "statusText": raw.get("gameStatusText") or ("Finale" if final else "In corso" if status == 2 else "In programma"),
                    "source": "NBA.com official CDN via GitHub Actions",
                    "sourceUrl": f"https://www.nba.com/game/{gid}", "updated": datetime.now(ZoneInfo("UTC")).isoformat(),
                }
                if final:
                    try:
                        box = get_json(f"{BASE}/boxscore/boxscore_{gid}.json").get("game", {})
                        for side in (box.get("homeTeam", {}), box.get("awayTeam", {})):
                            for p in side.get("players", []):
                                st = p.get("statistics", {})
                                mins = minutes(st.get("minutes"))
                                if mins is None or mins == 0:
                                    continue
                                pname = p.get("name") or " ".join(x for x in (p.get("firstName"), p.get("familyName")) if x)
                                pid = str(p.get("personId") or pname)
                                sid = f"{gid}_{pid}"
                                stats[sid] = {
                                    "id": sid, "gameId": gid, "player": pname, "playerId": pid,
                                    "season": season_for(game_date), "date": game_date,
                                    "team": side.get("teamTricode") or side.get("teamName", ""), "min": mins,
                                    "pts": st.get("points"), "reb": st.get("reboundsTotal"), "ast": st.get("assists"),
                                    "stl": st.get("steals"), "blk": st.get("blocks"),
                                    "source": "NBA.com official CDN via GitHub Actions",
                                }
                        time.sleep(0.35)
                    except Exception as exc:
                        print(f"Box score {gid} non disponibile: {exc}")
            print(f"{day.isoformat()}: {len(day_games)} partite")
        except Exception as exc:
            day_errors.append(f"{day.isoformat()}: {exc}")
            print(day_errors[-1], file=sys.stderr)
        time.sleep(0.35)
    if found_count == 0:
        raise RuntimeError("Nessuna partita ricevuta dal feed NBA. Archivio precedente lasciato invariato. " + " | ".join(day_errors))
    # Keep all previously collected records; merge this week's refreshed data.
    result = {
        "schema": 1, "updatedAt": datetime.now(ZoneInfo("UTC")).isoformat(),
        "weekStart": dates[0].isoformat(), "weekEnd": dates[-1].isoformat(),
        "games": sorted(games.values(), key=lambda x: (x.get("date", ""), x.get("id", ""))),
        "playerStats": sorted(stats.values(), key=lambda x: (x.get("date", ""), x.get("player", ""))),
        "collection": {"daysRead": 7-len(day_errors), "daysFailed": len(day_errors), "gamesInCurrentWeek": found_count},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(OUT)
    print(f"OK: {found_count} partite questa settimana; archivio totale {len(result['games'])} partite e {len(result['playerStats'])} righe giocatore.")
    if day_errors:
        print("ATTENZIONE: alcuni giorni non sono stati letti: " + " | ".join(day_errors))

if __name__ == "__main__":
    main()
