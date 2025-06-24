from typing import Optional


from core.deal_enums import SpecialBid, BiddingSuit, Direction

'''
    C - Clubs (trefl)
    D - Diamonds (karo)
    H - Hearts (kier)
    S - Spades (pik)
    NT - No trump (bez atu)
'''
LEGAL_BIDS = [
    "PASS",
    "1C",
    "1D",
    "1H",
    "1S",
    "1NT",
    "2C",
    "2D",
    "2H",
    "2S",
    "2NT",
    "3C",
    "3D",
    "3H",
    "3S",
    "3NT",
    "4C",
    "4D",
    "4H",
    "4S",
    "4NT",
    "5C",
    "5D",
    "5H",
    "5S",
    "5NT",
    "6C",
    "6D",
    "6H",
    "6S",
    "6NT",
    "7C",
    "7D",
    "7H",
    "7S",
    "7NT",
    "X",
    "XX",
]

_LEGAL_BIDS_SET = set(LEGAL_BIDS)



class BridgeBid:
    def __init__(self, level: int = None, suit: BiddingSuit = None, special: SpecialBid = None):
        """
        Reprezentuje zgłoszenie w licytacji. Może to być:
        1. Normalne zgłoszenie (np. 1H, 2NT).
        2. Specjalna akcja (PASS, DOUBLE, REDOUBLE).
        """

        self.level = level
        self.suit = suit
        self.special = special

    @classmethod
    def from_str(cls, bid: str) -> "BridgeBid":
        bid = bid.upper()
        if bid not in _LEGAL_BIDS_SET:
            raise ValueError("Provide either a proper bid (level & suit) or a special action (PASS, DOUBLE, REDOUBLE).")

        if bid in ["PASS", "X", "XX"]:
            return BridgeBid(special=SpecialBid.from_str(bid))
        else:
            level = int(bid[0])
            suit = bid[1:]
            return BridgeBid(level=level, suit=BiddingSuit.from_str(suit))

    def __repr__(self):
        if self.special:
            return str(self.special)
        return f"{self.level}{self.suit}"

    def __str__(self):
        if self.special:
            return str(self.special)
        return f"{self.level} {self.suit}"


    def is_higher_than(self, other: Optional['BridgeBid']) -> bool:
        """
        Porównuje, czy bieżące zgłoszenie jest wyższe od innego.
        Specjalne zgłoszenia (PASS, DOUBLE, REDOUBLE) są ignorowane w porównaniu.
        """
        if not other:
            return True

        if self.special or other.special:
            raise ValueError("Cannot compare bidding levels for special actions like PASS, DOUBLE, or REDOUBLE.")

        if self.level > other.level:
            return True
        elif self.level == other.level:
            return self.suit.value > other.suit.value
        return False

