"""Standard founder vesting (4 years, 1-year cliff, monthly after) and the 83(b) deadline."""
from datetime import date, timedelta


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m + 1
    # clamp to the last day of the month (e.g. Jan 31 + 1 month -> Feb 28/29)
    for day in (d.day, 30, 29, 28):
        try:
            return date(year, month, day)
        except ValueError:
            continue


def vested_units(total: int, start: date, on: date, months=48, cliff_months=12) -> int:
    """Units vested on a given date. Nothing before the cliff, then monthly."""
    if on < add_months(start, cliff_months):
        return 0
    elapsed = 0
    while elapsed < months and add_months(start, elapsed + 1) <= on:
        elapsed += 1
    return total if elapsed >= months else total * elapsed // months


def milestones(start: date, months=48, cliff_months=12) -> dict:
    return {"cliff": add_months(start, cliff_months), "fully_vested": add_months(start, months)}


def deadline_83b(grant: date, holidays=()) -> date:
    """
    An 83(b) election must be filed within 30 days of the grant. If day 30 lands on a
    weekend or a listed federal holiday, the deadline moves to the next business day
    (IRC section 7503). Pass holidays as a set of dates.
    """
    d = grant + timedelta(days=30)
    while d.weekday() >= 5 or d in set(holidays):
        d += timedelta(days=1)
    return d


def schedule(total: int, start: date, months=48, cliff_months=12) -> list:
    """Vested balance at the cliff and every 6 months after, for a quick table."""
    out = []
    for m in range(cliff_months, months + 1, 6):
        d = add_months(start, m)
        out.append({"date": d.isoformat(), "vested": vested_units(total, start, d, months, cliff_months)})
    return out
