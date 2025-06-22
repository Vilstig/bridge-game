import pytest

from core import Card, BiddingSuit, Direction
from core.play_utils import evaluate_trick_winner


# Helper to make cards quickly
def card(card_str: str) -> Card:
    return Card.from_str(card_str)

def suit(suit_str: str) -> BiddingSuit:
    return BiddingSuit.from_str(suit_str)

def test_leading_suit_highest_card_wins():
    trick = [
        (Direction.NORTH, card("H5")),
        (Direction.EAST, card("H3")),
        (Direction.SOUTH, card("HK")),
        (Direction.WEST, card("H9")),
    ]
    trump = suit("S")  # Hearts is not trump
    winner = evaluate_trick_winner(trick, trump)
    assert winner == card("HK")

def test_trump_card_wins_over_lead_suit():
    trick = [
        (Direction.NORTH, card("H5")),
        (Direction.EAST, card("H3")),
        (Direction.SOUTH, card("S2")),  # Trump
        (Direction.WEST, card("H9")),
    ]
    trump = suit("S")
    winner = evaluate_trick_winner(trick, trump)
    assert winner == card("s2")

def test_multiple_trump_cards_highest_trump_wins():
    trick = [
        (Direction.NORTH, card("D5")),
        (Direction.EAST, card("S2")),
        (Direction.SOUTH, card("SK")),
        (Direction.WEST, card("SQ")),
    ]
    trump = suit("S")
    winner = evaluate_trick_winner(trick, trump)
    assert winner == card("SK")

def test_no_trump_highest_lead_suit_wins():
    trick = [
        (Direction.NORTH, card("D2")),
        (Direction.EAST, card("DK")),
        (Direction.SOUTH, card("DJ")),
        (Direction.WEST, card("DA")),
    ]
    trump = suit("C")  # Clubs is trump but not used
    winner = evaluate_trick_winner(trick, trump)
    assert winner == card("DA")

def test_non_lead_non_trump_card_loses():
    trick = [
        (Direction.NORTH, card("H7")),
        (Direction.EAST, card("H8")),
        (Direction.SOUTH, card("C2")),
        (Direction.WEST, card("H9")),
    ]
    trump = suit("S")  # Spades is trump
    winner = evaluate_trick_winner(trick, trump)
    assert winner == card("h9")
