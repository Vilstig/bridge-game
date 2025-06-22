import pytest
from core.play_utils import TeamScore  # adjust path as needed
from core.deal_enums import BiddingSuit

_HEARTS = BiddingSuit.from_str("H")
_NO_TRUMP = BiddingSuit.from_str("NT")

# ---- Test Cases ----

def test_score_update_game_won_and_rubber_finished():
    ts = TeamScore("NS")
    result1 = ts.update_score(level=4, suit=_HEARTS, doubled=0, tricks=10, game="game 1")
    assert result1 == "Game finished"
    assert ts.vulnerable is True
    assert ts.rubber_bonus == 200
    result2 = ts.update_score(level=4, suit=_HEARTS, doubled=0, tricks=10, game="game 2")
    assert result2 == "Rubber finished"
    assert ts.rubber_bonus == 700
    assert ts.score_sum() > 0

def test_score_update_undertricks_penalty_nonvulnerable():
    ts = TeamScore("EW")
    result = ts.update_score(level=3, suit=_HEARTS, doubled=0, tricks=7, game="game 1")  # Needed 9, got 7 (2 undertricks)
    assert result == "Continue game"
    assert ts.penalty_points == -100
    assert ts.score_sum() == -100

def test_score_update_undertricks_penalty_vulnerable_doubled():
    ts = TeamScore("EW")
    ts.vulnerable = True
    ts.update_score(level=5, suit=_NO_TRUMP, doubled=1, tricks=7, game="game 2")
    assert ts.penalty_points == -1100 #-(200 + 300 + 300 + 300)

def test_slam_bonus_grand_and_small():
    ts = TeamScore("NS")
    ts.update_score(level=6, suit=_HEARTS, doubled=0, tricks=12, game="game 1")
    assert ts.slam_bonus == 500
    ts.update_score(level=7, suit=_HEARTS, doubled=0, tricks=13, game="game 2")
    assert ts.slam_bonus == 2000  # 500 + 1500

def test_overtricks_scoring_doubled_and_redoubled():
    ts = TeamScore("NS")
    # Doubled: level 2 → needs 8 tricks, gets 10 → 2 overtricks
    ts.update_score(level=2, suit=_HEARTS, doubled=1, tricks=10, game="game 1")
    assert ts.overtrick_points == 50 + 2 * 100

    # Redoubled: level 1 → needs 7, gets 9 → 2 overtricks
    ts.update_score(level=1, suit=_HEARTS, doubled=2, tricks=9, game="game 2")
    assert ts.overtrick_points == 50 + 200 + 100 + 2 * 400  # previous + redouble calc

def test_score_sum_calculation():
    ts = TeamScore("NS")
    ts.game_points["game 1"] = 90
    ts.rubber_bonus = 500
    ts.penalty_points = -100
    ts.slam_bonus = 500
    ts.overtrick_points = 60
    assert ts.score_sum() == 90 + 500 + 500 + 60 - 100
