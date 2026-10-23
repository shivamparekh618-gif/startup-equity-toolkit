"""Split a departing holder's stake among buyers in proportion to what each paid."""


def split_by_payment(payments: dict, stake_units: int) -> dict:
    """
    payments: {buyer: dollars paid}
    stake_units: units being bought out (e.g. 10% of 1,000,000 = 100,000)

    Each buyer gets stake_units * paid / total_paid, rounded to whole units with the
    largest-remainder method so the pieces always add back up to stake_units exactly.
    """
    total = sum(payments.values())
    if total <= 0:
        raise ValueError("Total payments must be positive.")
    if stake_units <= 0:
        raise ValueError("Stake must be positive.")
    exact = {b: stake_units * p / total for b, p in payments.items()}
    units = {b: int(v) for b, v in exact.items()}
    leftover = stake_units - sum(units.values())
    for b in sorted(exact, key=lambda b: exact[b] - units[b], reverse=True)[:leftover]:
        units[b] += 1
    return units


def summary(payments: dict, stake_units: int, authorized_units: int) -> list:
    units = split_by_payment(payments, stake_units)
    total = sum(payments.values())
    rows = []
    for b, paid in sorted(payments.items(), key=lambda kv: kv[1], reverse=True):
        rows.append({
            "buyer": b, "paid": paid,
            "share_of_payments_pct": round(100 * paid / total, 2),
            "units": units[b],
            "fully_diluted_pct": round(100 * units[b] / authorized_units, 3),
            "price_per_unit": round(paid / units[b], 5) if units[b] else None,
        })
    return rows
