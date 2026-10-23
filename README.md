# Startup Equity Toolkit

[![tests](https://github.com/shivamparekh618-gif/startup-equity-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/shivamparekh618-gif/startup-equity-toolkit/actions/workflows/tests.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![No dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)

**Who actually controls this company, what does each founder own after a co-founder leaves, and when is everyone's 83(b) due?**

Early-stage teams usually keep their cap table in a group chat and a spreadsheet that nobody fully trusts. That works until someone leaves, a few founders buy out their stake, and suddenly five different documents need to show the same numbers to the exact unit. This toolkit takes one config file and produces a cap table, a control report, a vesting and 83(b) calendar, buyout math that always adds up, and a members' consent drafted from the same numbers.

> **Why I built this.** I'm CLO and CFO at [LetsNavi](https://letsnavi.com/), where I handled our LLC formation and an equity restructure: removing inactive founders, splitting a departing co-founder's stake among the buyers by what each one paid, and getting more than a dozen agreements to show the same numbers. I wrote the math as code so I'd stop checking it by hand. This repo is a cleaned-up version with a **fictional company**. It contains no LetsNavi names, numbers or documents.

### At a glance

| | |
|---|---|
| **Problem** | Cap tables live in spreadsheets that drift out of sync with the legal documents |
| **Input** | One JSON file: holders, founder units, vesting start, and an optional buyout |
| **Built** | Cap table model with validation, buyout splitter, vesting and 83(b) calculator, Markdown and CSV output |
| **Tested** | 14 unit and end-to-end tests, run on every push by GitHub Actions |
| **Key insight** | A 45% holder controls 57% of the vote, because unissued reserve Units don't vote |

---

## Run it

Python 3.10+, standard library only.

```bash
git clone https://github.com/shivamparekh618-gif/startup-equity-toolkit.git
cd startup-equity-toolkit

python run.py                                      # sample company -> output/
python run.py --config examples/sample_company.json --out output/
python -m unittest -v                              # 14 tests
```

Outputs in `output/`:

| File | What's in it |
|---|---|
| [`cap_table.md`](output/cap_table.md) | Cap table, control report, vesting calendar, 83(b) deadlines, buyout breakdown |
| [`members_consent.md`](output/members_consent.md) | A members' written consent drafted from the same numbers |
| [`cap_table.csv`](output/cap_table.csv) | The cap table for a spreadsheet |

## What it does

```
company.json ─► validate ─► apply buyout ─► cap table + control report ─► vesting / 83(b) ─► Markdown + CSV
```

1. **Validates the table** ([`equity/captable.py`](equity/captable.py)). It catches issued Units exceeding authorized, reserve commitments exceeding the reserve, duplicate holders, and founder Units with no vesting start date. A bad table stops the run instead of producing a wrong document.
2. **Splits a buyout by payment** ([`equity/buyout.py`](equity/buyout.py)). Each buyer gets `stake × paid ÷ total paid`. Rounding to whole Units uses the largest-remainder method, so the pieces always add back up to the exact stake. Naive rounding can create or lose a Unit, and that's the kind of error that shows up later as two documents that disagree.
3. **Reports control, not just ownership.** Fully diluted % and voting % are different numbers. The report shows who can pass a majority vote alone and the smallest group that clears a 66% supermajority.
4. **Builds the vesting calendar** ([`equity/vesting.py`](equity/vesting.py)). It uses 4-year vesting with a 1-year cliff and monthly vesting after, with month-end dates clamped correctly. It also computes the **83(b) deadline**: 30 days from the grant, moved to the next business day if day 30 falls on a weekend (IRC §7503).
5. **Writes the documents** ([`equity/docs.py`](equity/docs.py)). Everything is generated from one source, so the cap table and the consent can't disagree.

## Example: the vote nobody noticed

The sample company has a CEO with 40% founder equity who buys 5.3% of a departing co-founder's stake. On paper she owns **45.3%**.

But 20% of the company is unissued reserve, and reserve Units don't vote. Of the Units that actually vote, she holds **56.7%**. She can pass any majority decision alone, and she plus the CTO clear a 66% supermajority without anyone else.

That isn't necessarily a problem. It is something every founder should see before signing, and it never appears in a spreadsheet that only has a "%" column. If the team wants to check it, the fix goes in the operating agreement, for example by requiring Major Decisions to also be approved by two members other than the CEO.

## Assumptions

- Units are a single class with identical economic rights. This matters for LLCs taxed as S corporations, which can only have one class of stock.
- Founder Units vest over 48 months with a 12-month cliff. Purchased Units are fully vested.
- Unissued reserve Units carry no vote.
- Weekends move the 83(b) deadline. Federal holidays can be passed in as a list.

## Limitations

- **Not legal or tax advice.** The consent is a draft for discussion. A lawyer should review anything before anyone signs.
- **One share class.** No preferred stock, SAFEs, convertible notes or option pools with strike prices. Those would be the next additions if a company raises a priced round.
- **No acceleration modeling.** Single- or double-trigger acceleration on a sale isn't simulated yet.

## Project layout

```
run.py                  entry point: load -> validate -> buyout -> outputs
equity/
  captable.py           holders, validation, fully diluted vs voting, control report
  buyout.py             payment-weighted split with exact rounding
  vesting.py            vesting schedule, cliff, 83(b) deadline
  docs.py               Markdown cap table, members' consent, CSV
examples/               fictional sample company
tests/                  unit + end-to-end tests
output/                 outputs from the last run
```
