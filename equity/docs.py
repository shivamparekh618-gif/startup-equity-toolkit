"""Render the cap table and a members' consent as Markdown, plus a CSV export."""
import csv
from datetime import date

from .captable import CapTable
from . import vesting


def _money(x):
    return f"${x:,.2f}" if x else "—"


def cap_table_md(ct: CapTable, grant: date, buyout_rows=None, seller=None) -> str:
    lines = [f"# {ct.company}: Cap Table", "",
             f"{ct.authorized_units:,} Units authorized (100% fully diluted). "
             f"{ct.outstanding:,} issued, {ct.reserve:,} in reserve.", "",
             "| Holder | Role | Founder Units | Purchased Units | Total | Fully diluted | Voting | Paid |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in ct.rows():
        lines.append(f"| {r['holder']} | {r['role']} | {r['founder_units']:,} | {r['purchased_units']:,} | "
                     f"{r['total_units']:,} | {r['fully_diluted_pct']:.3f}% | {r['voting_pct']:.2f}% | {_money(r['paid'])} |")
    lines.append(f"| Reserve (unissued) | | | | {ct.reserve:,} | {100 * ct.reserve / ct.authorized_units:.3f}% | doesn't vote | |")
    if ct.committed:
        for name, u in ct.committed.items():
            lines.append("")
            lines.append(f"{u:,} reserve Units are committed to {name}.")

    c = ct.control_report()
    lines += ["", "## Control", ""]
    if c["solo_majority"]:
        lines.append(f"- **{', '.join(c['solo_majority'])}** can pass any majority vote alone.")
    else:
        lines.append("- No single holder controls a majority vote.")
    lines.append(f"- Smallest group that clears a 66% supermajority: **{', '.join(c['supermajority_group'])}** "
                 f"({c['supermajority_group_pct']}% of votes).")
    lines.append("- Voting power is higher than the fully diluted % because reserve Units don't vote.")

    lines += ["", "## Vesting and 83(b)", "",
              "| Holder | Founder Units | Vesting start | Cliff | Fully vested | 83(b) deadline |",
              "|---|---:|---|---|---|---|"]
    for h in ct.holders:
        if h.founder_units:
            start = date.fromisoformat(h.vesting_start)
            m = vesting.milestones(start)
            lines.append(f"| {h.name} | {h.founder_units:,} | {start} | {m['cliff']} | {m['fully_vested']} | "
                         f"{vesting.deadline_83b(grant)} |")

    if buyout_rows:
        lines += ["", f"## Buyout of {seller}", "",
                  "| Buyer | Paid | Share of payments | Units | Fully diluted | Price per Unit |",
                  "|---|---:|---:|---:|---:|---:|"]
        for r in buyout_rows:
            lines.append(f"| {r['buyer']} | {_money(r['paid'])} | {r['share_of_payments_pct']}% | {r['units']:,} | "
                         f"{r['fully_diluted_pct']:.3f}% | ${r['price_per_unit']} |")
    return "\n".join(lines) + "\n"


def members_consent_md(ct: CapTable, effective: date, seller=None, buyout_rows=None) -> str:
    voters = [h.name for h in ct.holders if h.founder_units]
    lines = [f"# Action by Written Consent of the Members of {ct.company}", "",
             f"**Effective Date:** {effective:%B} {effective.day}, {effective.year}", "",
             "> Template output for illustration. Not legal advice. Have counsel review before anyone signs.", "",
             "The undersigned Members adopt the following resolutions by written consent.", "",
             "## 1. Capitalization", "",
             f"RESOLVED, that the Company's equity is expressed in Units, with {ct.authorized_units:,} Units "
             "representing 100% on a fully diluted basis, and that the Company's capitalization is as set out in "
             "the attached cap table.", "",
             "## 2. Founder Units", "",
             "RESOLVED, that the following Founder Units are issued, each vesting over 48 months with a 12-month cliff:", ""]
    for h in ct.holders:
        if h.founder_units:
            lines.append(f"- {h.name}: {h.founder_units:,} Units, vesting from {h.vesting_start}")
    if buyout_rows:
        lines += ["", f"## 3. Buyout of {seller}", "",
                  f"RESOLVED, that the transfer of {seller}'s interest to the buyers below, for the prices they paid, "
                  "is approved and any right of first refusal is waived:", ""]
        for r in buyout_rows:
            lines.append(f"- {r['buyer']}: {r['units']:,} Units for {_money(r['paid'])}")
    lines += ["", "## Signatures", ""]
    for v in voters:
        lines += [f"**{v.upper()}**", "", "Signature: ______________________   Date: __________", ""]
    return "\n".join(lines)


def write_csv(ct: CapTable, path: str):
    rows = ct.rows()
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
