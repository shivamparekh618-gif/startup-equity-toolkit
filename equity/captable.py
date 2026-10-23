"""Cap table model: who owns what, on a fully diluted and a voting basis."""
from dataclasses import dataclass, field


@dataclass
class Holder:
    name: str
    role: str = ""
    founder_units: int = 0      # issued for services, subject to vesting
    purchased_units: int = 0    # bought for cash, fully vested
    paid: float = 0.0           # cash paid for purchased units
    vesting_start: str = ""     # ISO date, for founder units

    @property
    def total(self) -> int:
        return self.founder_units + self.purchased_units


@dataclass
class CapTable:
    company: str
    authorized_units: int
    holders: list = field(default_factory=list)
    committed: dict = field(default_factory=dict)   # name -> units promised from the reserve later

    @property
    def outstanding(self) -> int:
        return sum(h.total for h in self.holders)

    @property
    def reserve(self) -> int:
        return self.authorized_units - self.outstanding

    def validate(self) -> list:
        """Return a list of problems. An empty list means the table is consistent."""
        problems = []
        if self.outstanding > self.authorized_units:
            problems.append(f"Issued units ({self.outstanding:,}) exceed authorized ({self.authorized_units:,}).")
        if sum(self.committed.values()) > self.reserve:
            problems.append("Units committed from the reserve exceed the reserve.")
        names = [h.name for h in self.holders]
        if len(names) != len(set(names)):
            problems.append("Duplicate holder names.")
        for h in self.holders:
            if h.founder_units < 0 or h.purchased_units < 0:
                problems.append(f"{h.name} has negative units.")
            if h.founder_units and not h.vesting_start:
                problems.append(f"{h.name} has founder units but no vesting start date.")
        return problems

    def fully_diluted_pct(self, h: Holder) -> float:
        return 100 * h.total / self.authorized_units

    def voting_pct(self, h: Holder) -> float:
        """Unissued reserve units don't vote, so voting power is share of outstanding units."""
        return 100 * h.total / self.outstanding if self.outstanding else 0.0

    def control_report(self, majority=50.0, supermajority=66.0) -> dict:
        """Who can pass votes alone, and the smallest group that clears the supermajority."""
        ranked = sorted(self.holders, key=lambda h: h.total, reverse=True)
        solo_majority = [h.name for h in ranked if self.voting_pct(h) > majority]
        group, running = [], 0.0
        for h in ranked:
            group.append(h.name)
            running += self.voting_pct(h)
            if running >= supermajority:
                break
        return {"solo_majority": solo_majority, "supermajority_group": group,
                "supermajority_group_pct": round(running, 2)}

    def rows(self) -> list:
        out = []
        for h in sorted(self.holders, key=lambda h: h.total, reverse=True):
            out.append({
                "holder": h.name, "role": h.role,
                "founder_units": h.founder_units, "purchased_units": h.purchased_units,
                "total_units": h.total,
                "fully_diluted_pct": round(self.fully_diluted_pct(h), 3),
                "voting_pct": round(self.voting_pct(h), 2),
                "paid": h.paid,
            })
        return out


def from_dict(d: dict) -> CapTable:
    holders = [Holder(**h) for h in d["holders"]]
    return CapTable(company=d["company"], authorized_units=d["authorized_units"],
                    holders=holders, committed=d.get("committed", {}))
