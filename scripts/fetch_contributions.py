#!/usr/bin/env python3
"""
Scrape real daily contribution counts from GitHub's public, unauthenticated
contributions endpoint and write data/contributions.json with raw days plus
derived stats (current streak, longest streak, best day, monthly totals).

No token, no auth, no GraphQL -- just the public HTML GitHub already serves.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "vanz-0")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found -- github markup may have changed", file=sys.stderr)
        sys.exit(1)

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        td_id = td.get("id")
        tooltip_el = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        text = tooltip_el.get_text(strip=True) if tooltip_el else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"(\d+)", text)
            count = int(m.group(1)) if m else 0
        days.append({"date": date, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_current_streak(days):
    """Count consecutive days with >= 1 contribution ending today (or yesterday)."""
    today = datetime.date.today()
    streak = 0
    for d in reversed(days):
        dt = datetime.date.fromisoformat(d["date"])
        if dt > today:
            continue
        if d["count"] > 0:
            streak += 1
        else:
            # allow today to be zero (day not over yet)
            if dt == today and streak == 0:
                continue
            break
    return streak


def compute_longest_streak(days):
    best = 0
    cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def compute_stats(days):
    total = sum(d["count"] for d in days)
    best_day = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}

    # monthly totals
    monthly = {}
    for d in days:
        month_key = d["date"][:7]  # "YYYY-MM"
        monthly[month_key] = monthly.get(month_key, 0) + d["count"]

    return {
        "total": total,
        "current_streak": compute_current_streak(days),
        "longest_streak": compute_longest_streak(days),
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly": monthly,
    }


def main():
    print(f"Fetching contributions for {USERNAME}...")
    days = fetch_days()
    stats = compute_stats(days)
    out = {"days": days, "stats": stats}

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote {len(days)} days, {stats['total']} total contributions to {OUT_PATH}")
    print(f"  Current streak: {stats['current_streak']} days")
    print(f"  Longest streak: {stats['longest_streak']} days")
    print(f"  Best day: {stats['best_day']['date']} ({stats['best_day']['count']})")


if __name__ == "__main__":
    main()
