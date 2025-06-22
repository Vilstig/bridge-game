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

    def verify_legality(self, previous_bid: Optional["BridgeBid"], new_bid_direction: Direction,
                        contract_direction: Direction) -> bool:
        """
        Sprawdza legalność nowego zgłoszenia w brydżu w odniesieniu do poprzedniego zgłoszenia.

        :param previous_bid: Poprzednie zgłoszenie w licytacji (może być None, jeśli nowy gracz zaczyna licytację).
        :param new_bid_direction: Kierunek gracza składającego nowe zgłoszenie (np. 'N', 'E', 'S', 'W').
        :param contract_direction: Kierunek gracza, który zgłosił aktualny kontrakt.
        :return: True, jeśli zgłoszenie jest legalne; False, jeśli jest nielegalne.
        """
        # Jeśli nie ma wcześniejszego zgłoszenia, każde nowe zgłoszenie (ale nie kontra/rekontra) jest legalne
        if previous_bid is None:
            if self.special in {SpecialBid.DOUBLE, SpecialBid.REDOUBLE}:
                return False  # Pierwszym zgłoszeniem nie może być DOUBLE ani REDOUBLE
            return True

        # Przypadek 1: Jeśli nowe zgłoszenie to PASS, zawsze jest legalne
        if self.special == SpecialBid.PASS:
            return True

        # Przypadek 2: Jeśli nowe zgłoszenie to DOUBLE (kontra)
        if self.special == SpecialBid.DOUBLE:
            # DOUBLE jest legalne, gdy poprzednie zgłoszenie pochodziło od przeciwnika i nie było kontrą ani rekontrą
            if previous_bid.special is None and contract_direction.partner() is not new_bid_direction:
                return True
            return False

        # Przypadek 3: Jeśli nowe zgłoszenie to REDOUBLE (rekontra)
        if self.special == SpecialBid.REDOUBLE:
            # REDOUBLE jest legalne, gdy poprzednie zgłoszenie było DOUBLE i pochodziło od przeciwnika
            if previous_bid.special == SpecialBid.DOUBLE and (contract_direction.partner() is new_bid_direction) or (contract_direction is new_bid_direction):
                return True
            return False

        # Przypadek 4: Jeśli nowe zgłoszenie to normalna licytacja (np. 1H, 2NT, itd.)
        if previous_bid.special is None:
            # Jeśli poprzednie zgłoszenie to zwykła licytacja, nowe zgłoszenie musi być wyższe
            return self.is_higher_than(previous_bid)

        # Jeśli poprzednie zgłoszenie to DOUBLE lub REDOUBLE, nowe zgłoszenie nie może być niższe
        return self.is_higher_than(previous_bid)

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

