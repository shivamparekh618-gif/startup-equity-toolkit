"""Build the cap table, apply any buyout, and write the outputs.

    python run.py                                   # uses examples/sample_company.json
    python run.py --config path/to/your_company.json
"""
import argparse
import json
import os
from datetime import date

from equity.captable import from_dict
from equity import buyout, docs

HERE = os.path.dirname(os.path.abspath(__file__))


def build(config_path):
    with open(config_path) as f:
        cfg = json.load(f)
    ct = from_dict(cfg)
    rows, seller = None, None
    if "buyout" in cfg:
        b = cfg["buyout"]
        seller = b["seller"]
        rows = buyout.summary(b["payments"], b["stake_units"], ct.authorized_units)
        by_name = {h.name: h for h in ct.holders}
        for r in rows:
            h = by_name[r["buyer"]]
            h.purchased_units += r["units"]
            h.paid += r["paid"]
    problems = ct.validate()
    if problems:
        raise SystemExit("Cap table problems:\n- " + "\n- ".join(problems))
    return cfg, ct, rows, seller


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "examples", "sample_company.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "output"))
    args = ap.parse_args()

    cfg, ct, rows, seller = build(args.config)
    eff = date.fromisoformat(cfg["effective_date"])
    os.makedirs(args.out, exist_ok=True)
    open(os.path.join(args.out, "cap_table.md"), "w").write(docs.cap_table_md(ct, eff, rows, seller))
    open(os.path.join(args.out, "members_consent.md"), "w").write(docs.members_consent_md(ct, eff, seller, rows))
    docs.write_csv(ct, os.path.join(args.out, "cap_table.csv"))

    print(f"{ct.company}: {ct.outstanding:,} issued / {ct.authorized_units:,} authorized\n")
    print(f"{'Holder':<16}{'Units':>10}{'Diluted':>10}{'Voting':>9}")
    for r in ct.rows():
        print(f"{r['holder']:<16}{r['total_units']:>10,}{r['fully_diluted_pct']:>9.2f}%{r['voting_pct']:>8.2f}%")
    print(f"{'Reserve':<16}{ct.reserve:>10,}{100 * ct.reserve / ct.authorized_units:>9.2f}%{'—':>9}")
    c = ct.control_report()
    print(f"\nSolo majority: {', '.join(c['solo_majority']) or 'nobody'}")
    print(f"Supermajority group: {', '.join(c['supermajority_group'])} ({c['supermajority_group_pct']}%)")
    print(f"\nWrote cap_table.md, members_consent.md, cap_table.csv to {args.out}")


if __name__ == "__main__":
    main()
