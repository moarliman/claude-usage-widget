#!/usr/bin/env python3
"""Live CLI widget for Claude Code usage."""
import argparse
import sys
import time
from datetime import datetime, date, timedelta

from fetch_usage import RateLimited, fetch_usage, get_token

BAR_WIDTH = 40

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
RED = "\x1b[31m"
CLEAR = "\x1b[2J\x1b[H"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"


def color_for(util):
    if util < 0.5:
        return GREEN
    if util < 0.8:
        return YELLOW
    return RED


def working_days_progress():
    """Return (elapsed, total) working days in the current month."""
    today = date.today()
    year, month = today.year, today.month
    total = 0
    elapsed = 0
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            total += 1
            if d <= today:
                elapsed += 1
        d += timedelta(days=1)
    return elapsed, total


def next_month_first():
    today = date.today()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def render_bar(color, util, wd_frac):
    filled = int(round(util * BAR_WIDTH))
    marker = min(int(round(wd_frac * BAR_WIDTH)), BAR_WIDTH - 1)

    def colored_chars(start, end):
        if start >= end:
            return ""
        parts = []
        cur = None
        for i in range(start, end):
            c = color if i < filled else DIM
            if c != cur:
                parts.append(c)
                cur = c
            parts.append("█" if i < filled else "░")
        return "".join(parts)

    before = colored_chars(0, marker)
    after = colored_chars(marker + 1, BAR_WIDTH)
    after_lead = color if marker + 1 < filled else DIM
    if after:
        return f"{before}{RESET}|{after_lead}{after}{RESET}"
    return f"{before}{RESET}|{RESET}"


def render(usage, status_line):
    eu = usage.get("extra_usage") or {}
    used_cents = eu.get("used_credits") or 0
    limit_cents = eu.get("monthly_limit") or 0
    util = (used_cents / limit_cents) if limit_cents else 0

    color = color_for(util)
    wd_elapsed, wd_total = working_days_progress()
    wd_frac = wd_elapsed / wd_total if wd_total else 0
    bar = render_bar(color, util, wd_frac)

    used = f"${used_cents / 100:,.2f}"
    limit = f"${limit_cents / 100:,.2f}"
    pct = f"{util * 100:.1f}%"
    reset_date = next_month_first().strftime("%b %-d")
    wd_label = f"wd {wd_elapsed}/{wd_total}"

    return "\n".join([
        "",
        f"  {BOLD}Claude Code Usage{RESET}",
        "",
        f"  {used} / {limit}    {color}{pct} used{RESET}    {DIM}resets {reset_date}  {wd_label}{RESET}",
        f"  {bar}",
        "",
        f"  {DIM}{status_line} · Ctrl+C to exit{RESET}",
        "",
    ])


def main():
    parser = argparse.ArgumentParser(description="Live Claude Code usage widget")
    parser.add_argument("-i", "--interval", type=int, default=120,
                        help="refresh interval in seconds (default: 120)")
    args = parser.parse_args()

    sys.stdout.write(HIDE_CURSOR)
    last_usage = None
    last_updated = None
    try:
        while True:
            sleep_for = args.interval
            note = None
            try:
                last_usage = fetch_usage(get_token())
                last_updated = datetime.now().strftime("%H:%M:%S")
            except RateLimited as e:
                sleep_for = max(e.retry_after, args.interval)
                note = f"{YELLOW}rate limited, retrying in {sleep_for}s{RESET}"
            except Exception as e:
                note = f"{RED}error: {e}{RESET}"

            if last_usage is None:
                output = f"\n  {note or 'Loading...'}\n"
            else:
                status = f"Refreshes every {args.interval}s · Last updated {last_updated or '—'}"
                if note:
                    status = f"{status} · {note}{DIM}"
                output = render(last_usage, status)

            sys.stdout.write(CLEAR + output)
            sys.stdout.flush()
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
