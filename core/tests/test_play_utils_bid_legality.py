import pytest

from core import BiddingSuit
from core.bids import BridgeBid
from core.board_record import BridgeContract
from core.deal_enums import Direction, SpecialBid
from core.play_utils import is_bid_legal

test_suit = BiddingSuit.from_str("H")

def test_is_bid_legal_first_bid_pass():
    previous_bid = None
    last_contract = None
    new_bid = BridgeBid(special=SpecialBid.PASS)
    new_bid_direction = Direction.NORTH

    assert is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_first_bid_double_not_legal():
    previous_bid = None
    last_contract = None
    new_bid = BridgeBid(special=SpecialBid.DOUBLE)
    new_bid_direction = Direction.NORTH

    assert not is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_first_bid_redouble_not_legal():
    previous_bid = None
    last_contract = None
    new_bid = BridgeBid(special=SpecialBid.REDOUBLE)
    new_bid_direction = Direction.NORTH

    assert not is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_pass_after_bid():
    previous_bid = BridgeBid(level=1, suit=test_suit)
    last_contract = None
    new_bid = BridgeBid(special=SpecialBid.PASS)
    new_bid_direction = Direction.EAST

    assert is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_double_when_legal():
    previous_bid = BridgeBid(level=1, suit=test_suit)
    last_contract = BridgeContract(level=1, suit=test_suit, declarer=Direction.NORTH, doubled=0)
    new_bid = BridgeBid(special=SpecialBid.DOUBLE)
    new_bid_direction = Direction.EAST

    assert is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_double_when_not_legal():
    previous_bid = BridgeBid(level=1, suit=test_suit)
    last_contract = BridgeContract(level=1, suit=test_suit, declarer=Direction.EAST, doubled=0)
    new_bid = BridgeBid(special=SpecialBid.DOUBLE)
    new_bid_direction = Direction.WEST

    assert not is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_redouble_when_legal():
    previous_bid = BridgeBid(special=SpecialBid.DOUBLE)
    last_contract = BridgeContract(level=1, suit=test_suit, declarer=Direction.NORTH, doubled=0)
    new_bid = BridgeBid(special=SpecialBid.REDOUBLE)
    new_bid_direction = Direction.NORTH

    assert is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_redouble_when_not_legal():
    previous_bid = BridgeBid(special=SpecialBid.DOUBLE)
    last_contract = BridgeContract(level=1, suit=test_suit, declarer=Direction.EAST, doubled=0)
    new_bid = BridgeBid(special=SpecialBid.REDOUBLE)
    new_bid_direction = Direction.SOUTH

    assert not is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_higher_normal_bid():
    previous_bid = BridgeBid(level=1, suit=test_suit)
    last_contract = None
    new_bid = BridgeBid(level=2, suit=test_suit)
    new_bid_direction = Direction.WEST

    assert is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)


def test_is_bid_legal_lower_normal_bid_not_legal():
    previous_bid = BridgeBid(level=2, suit=test_suit)
    last_contract = None
    new_bid = BridgeBid(level=1, suit=test_suit)
    new_bid_direction = Direction.SOUTH

    assert not is_bid_legal(previous_bid, last_contract, new_bid, new_bid_direction)
