from __future__ import annotations

from typing import Optional

from core import BridgeBid
from core.deal_enums import BiddingSuit, Direction, SpecialBid


class BridgeContract:
    level: int
    suit: Optional[BiddingSuit]
    doubled: int
    declarer: Direction

    def __init__(self, level: int, suit: Optional[BiddingSuit], doubled: int, declarer: Optional[Direction]):
        self.level = level
        self.suit = suit
        self.doubled = doubled
        self.declarer = declarer

    @staticmethod
    def empty_contract() -> BridgeContract:
        return BridgeContract(0, None, 0, None)

    def update_from_bridge_bid(self, bid: 'BridgeBid', declarer: Direction) -> None:
        if bid.special and bid.special != SpecialBid.PASS:
            self.doubled += 1
        elif not bid.special:
            self.level = bid.level
            self.suit = bid.suit
            self.doubled = 0
            self.declarer = declarer

    def __str__(self) -> str:
        if self.level == 0:
            return "PASS"
        contract_str = str(self.level) + self.suit.abbreviation()
        for i in range(self.doubled):
            contract_str += "X"
        contract_str += f' {self.declarer.abbreviation()}'
        return contract_str

