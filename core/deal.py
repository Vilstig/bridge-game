from __future__ import annotations

from functools import total_ordering
from typing import Dict, Iterable, List

from core.deal_enums import Direction, Rank, Suit

"""
Classes to represent each component of a bridge deal
"""


@total_ordering
class Card:
    """
    A single card in a hand or deal of bridge
    """

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank
        self.image_path = f"assets/PNG-cards/{self.suit.name[0]}{self.rank.value[1]}.png"  # Przykład: "assets/PNG-cards/SA.png"

    def __eq__(self, other) -> bool:
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    def __lt__(self, other) -> bool:
        return (self.suit, self.rank) < (other.suit, other.rank)

    def __str__(self) -> bool:
        return self.suit.name[0] + self.rank.value[1]

    def __repr__(self) -> str:
        return self.suit.name[0] + self.rank.value[1]

    @classmethod
    def from_str(cls, card_str) -> Card:
        return Card(Suit.from_str(card_str[0]), Rank.from_str(card_str[1]))

CUSTOM_SUIT_ORDER = [Suit.DIAMONDS, Suit.CLUBS, Suit.HEARTS, Suit.SPADES]

class PlayerHand:
    """
    A single player's 13 cards in a bridge deal
    """

    def __init__(self, suits: Dict[Suit, List[Rank]]):
        self.suits = suits
        assert 13 == sum([len(ranks) for suit, ranks in self.suits.items()])
        self.cards = []
        for suit in reversed(CUSTOM_SUIT_ORDER):
            for rank in self.suits[suit]:
                self.cards.append(Card(suit, rank))

    @staticmethod
    def from_string_lists(spades: List[str], hearts: List[str], diamonds: List[str], clubs: List[str]) -> PlayerHand:
        """
        Build a PlayerHand out of Lists of Strings which map to Ranks for each suit. e.g. ['A', 'T', '3'] to represent
        a suit holding of Ace, Ten, Three
        :return: PlayerHand representing the holdings provided by the arguments
        """
        suits = {
            Suit.SPADES: sorted([Rank.from_str(card_str) for card_str in spades], reverse=True),
            Suit.HEARTS: sorted([Rank.from_str(card_str) for card_str in hearts], reverse=True),
            Suit.DIAMONDS: sorted([Rank.from_str(card_str) for card_str in diamonds], reverse=True),
            Suit.CLUBS: sorted([Rank.from_str(card_str) for card_str in clubs], reverse=True),
        }
        return PlayerHand(suits)

    @staticmethod
    def from_cards(cards: Iterable[Card]) -> PlayerHand:
        suits = {
            Suit.CLUBS: sorted([card.rank for card in cards if card.suit == Suit.CLUBS], reverse=True),
            Suit.DIAMONDS: sorted([card.rank for card in cards if card.suit == Suit.DIAMONDS], reverse=True),
            Suit.HEARTS: sorted([card.rank for card in cards if card.suit == Suit.HEARTS], reverse=True),
            Suit.SPADES: sorted([card.rank for card in cards if card.suit == Suit.SPADES], reverse=True),
        }
        return PlayerHand(suits)

    def contains_suit(self, suit: Suit) -> bool:
        for card in self.cards:
            if card.suit == suit:
                return True
        return False

    def __repr__(self):
        suit_arrays = [[], [], [], []]
        for card in self.cards:
            suit_arrays[card.suit.value].append(repr(card))
        repr_str = " | ".join(" ".join(suit) for suit in reversed(suit_arrays))
        return f"PlayerHand({repr_str})"

    def __eq__(self, other) -> bool:
        return self.suits == other.suits

    def __hash__(self) -> int:
        return hash(set(self.cards))

