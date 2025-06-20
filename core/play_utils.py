from functools import partial
from typing import Callable, Optional, Dict, List, Tuple

from core.board_record import BridgeContract
from core.deal import Card, PlayerHand
from core.deal_enums import BiddingSuit, Suit, Direction


def validate_card_usage(card: Card, trick: List[Tuple[Direction, Card]], player_cards: PlayerHand) -> bool:
    if not trick:
        return True
    else:
        first_card_suit = trick[0][1].suit
        if player_cards.contains_suit(first_card_suit) and card.suit != first_card_suit:
            return False
        return True

def evaluate_trick_winner(trick: List[Tuple[Direction, Card]], trump_suit: BiddingSuit) -> Card:
    max_score = 0
    best_card = None

    for direction, card in trick:
        score = _evaluate_card(trump_suit, trick[0][1].suit, card)
        if score > max_score:
            best_card = card
            max_score = score

    return best_card



def _evaluate_card(trump_suit: BiddingSuit, suit_led: Suit, card: Card) -> int:
    """
    Score a card on its ability to win a trick given the trump suit and the suit that led to the trick
    :return: the card's score
    """
    score = card.rank.value[0]
    if card.suit == trump_suit.to_suit():
        score += 100
    elif card.suit != suit_led:
        score -= 100
    return score


def trick_evaluator(trump_suit: BiddingSuit, suit_led: Suit) -> Callable:
    """
    :return: a partial which takes a Card as an argument and returns an ordering score within the context of a trick in
    progress
    """
    return partial(_evaluate_card, trump_suit, suit_led)


_FIRST_TRICK_VALUE = {
    BiddingSuit.NO_TRUMP: 40,
    BiddingSuit.SPADES: 30,
    BiddingSuit.HEARTS: 30,
    BiddingSuit.DIAMONDS: 20,
    BiddingSuit.CLUBS: 20,
}
_TRICK_VALUE = {
    BiddingSuit.NO_TRUMP: 30,
    BiddingSuit.SPADES: 30,
    BiddingSuit.HEARTS: 30,
    BiddingSuit.DIAMONDS: 20,
    BiddingSuit.CLUBS: 20,
}


def _calculate_bonus(
    level: int, suit: BiddingSuit, doubled: int, vulnerable: bool, contracted_trick_score: int, overtricks: int
) -> int:
    score = 0
    # Slam bonus
    if level == 7:
        score += 1500 if vulnerable else 1000
    elif level == 6:
        score += 750 if vulnerable else 500

    # Game / part-score
    if contracted_trick_score >= 100:
        score += 500 if vulnerable else 200

    # Overtricks
    if doubled == 0:
        score += overtricks * _TRICK_VALUE[suit]
    elif doubled == 1:
        score += 50
        score += overtricks * (200 if vulnerable else 100)
    elif doubled == 2:
        score += 100
        score += overtricks * (400 if vulnerable else 200)
    return score


_FIRST_UNDERTRICK_VALUE = {
    (False, 0): 50,
    (False, 1): 100,
    (False, 2): 200,
    (True, 0): 100,
    (True, 1): 200,
    (True, 2): 400,
}

_SECOND_THIRD_UNDERTRICK_VALUE = {
    (False, 0): 50,
    (False, 1): 200,
    (False, 2): 400,
    (True, 0): 100,
    (True, 1): 300,
    (True, 2): 600,
}

_SUBSEQUENT_UNDERTRICK_VALUE = {
    (False, 0): 50,
    (False, 1): 300,
    (False, 2): 600,
    (True, 0): 100,
    (True, 1): 300,
    (True, 2): 600,
}


def calculate_score(level: int, suit: Optional[BiddingSuit], doubled: int, tricks: int, vulnerable: bool) -> int:
    """
    :param level: contract level (4 in 4S)
    :param suit: contract bidding suit
    :param doubled: 0=undoubled, 1=doubled, 2=redoubled
    :param tricks: tricks_log taken by declarer
    :param vulnerable: vulnerability of declarer
    :return: declarer's score
    """
    from core.board_record import Contract

    if level == 0:  # Pass Out
        return 0
    scoring_tricks = tricks - 6
    if scoring_tricks >= level:
        double_multiplier = pow(2, doubled)
        first_trick_score = _FIRST_TRICK_VALUE[suit] * double_multiplier
        subsequent_tricks_score = _TRICK_VALUE[suit] * double_multiplier * (level - 1)
        bonus = _calculate_bonus(
            level, suit, doubled, vulnerable, first_trick_score + subsequent_tricks_score, scoring_tricks - level
        )
        print(f'First trick: {first_trick_score}, subsequent tricks_log: {subsequent_tricks_score}, bonus: {bonus}')
        return first_trick_score + subsequent_tricks_score + bonus
    else:
        undertricks = level + 6 - tricks
        score_key = (vulnerable, doubled)
        score = 0
        for i in range(0, undertricks):
            score_dict = (
                _FIRST_UNDERTRICK_VALUE
                if i == 0
                else _SECOND_THIRD_UNDERTRICK_VALUE
                if 0 < i < 3
                else _SUBSEQUENT_UNDERTRICK_VALUE
            )
            score -= score_dict[score_key]
        return score


class TeamScore:
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.game_points = {'game 1': 0, 'game 2': 0, 'game 3': 0}
        self.rubber_bonus = 0
        self.slam_bonus = 0
        self.double_bonus = 0
        self.overtrick_points = 0
        self.penalty_points = 0
        self.vulnerable = False

    def __str__(self):
        header = (
            f"{'Team Name':<15} {'Game 1':<10} {'Game 2':<10} {'Game 3':<10} "
            f"{'Rubber':<10} {'Slam':<10} {'Double':<10} {'Overtricks':<10} "
            f"{'Penalty':<10} {'Sum':<10}"
        )

        data = (
            f"{self.team_name:<15} {self.game_points['game 1']:<10} {self.game_points['game 2']:<10} "
            f"{self.game_points['game 3']:<10} {self.rubber_bonus:<10} {self.slam_bonus:<10} "
            f"{self.double_bonus:<10} {self.overtrick_points:<10} {self.penalty_points:<10} "
            f"{self.score_sum() :<10}"
        )

        return f"{header}\n{data}"

    def update_score(self, level: int, suit: Optional[BiddingSuit], doubled: int, tricks: int, game: str) -> str:
        """
        Updates the game score based on the outcome of a bridge bidding and play scenario.

        This method evaluates the scoring of tricks_log won or lost in a bridge game round given the level of the
        contract, the suit being bid, any doubling penalties, and the number of tricks_log taken. It updates
        the player's game points and penalty points while also determining whether the game or rubber has
        been finished.

        Parameters:
        level (int): The level of the bid (1-7).
        suit (Optional[BiddingSuit]): The suit bid in the current game (e.g., Hearts, Spades, No Trump, etc.).
        doubled (int): An indication of whether the bid was undoubled (0), doubled (1), or redoubled (2).
        tricks_log (int): The total number of tricks_log taken by the team in this round.
        game (str): The identifier for the current game or hand being scored.

        Returns:
        str: A status string indicating whether the rubber or game has been finished or the game should
             continue. Possible values are 'Rubber finished', 'Game finished', or 'Continue game'.
        """
        scoring_tricks = tricks - 6
        if scoring_tricks >= level:
            double_multiplier = pow(2, doubled)
            first_trick_score = _FIRST_TRICK_VALUE[suit] * double_multiplier
            subsequent_tricks_score = _TRICK_VALUE[suit] * double_multiplier * (level - 1)
            self._update_bonus(level, suit, doubled, scoring_tricks - level)
            self.game_points[game] += first_trick_score + subsequent_tricks_score
            if self.game_points[game] >= 100:
                if self.vulnerable:
                    self.rubber_bonus += 500
                    return 'Rubber finished'
                else:
                    self.vulnerable = True
                    self.rubber_bonus += 200
                    return 'Game finished'
            return 'Continue game'
        else:
            undertricks = level + 6 - tricks
            score_key = (self.vulnerable, doubled)
            score = 0

            for i in range(undertricks):
                if i == 0:
                    score_dict = _FIRST_UNDERTRICK_VALUE
                elif i < 3:
                    score_dict = _SECOND_THIRD_UNDERTRICK_VALUE
                else:
                    score_dict = _SUBSEQUENT_UNDERTRICK_VALUE

                score += score_dict[score_key]

            self.penalty_points -= score
            return 'Continue game'


    def _update_bonus(self, level: int, suit: BiddingSuit, doubled: int, overtricks: int) -> None:
            # Slam bonus
            if level == 7:
                self.slam_bonus += 1500 if self.vulnerable else 1000
            elif level == 6:
                self.slam_bonus += 750 if self.vulnerable else 500

            # Overtricks
            if doubled == 0:
                self.overtrick_points += overtricks * _TRICK_VALUE[suit]
            elif doubled == 1:
                self.overtrick_points += 50
                self.overtrick_points += overtricks * (200 if self.vulnerable else 100)
            elif doubled == 2:
                self.overtrick_points += 100
                self.overtrick_points += overtricks * (400 if self.vulnerable else 200)

    def score_sum(self):
        score_sum = 0
        for game, points in self.game_points.items():
            score_sum += points
        return score_sum + self.rubber_bonus + self.slam_bonus + self.double_bonus + self.overtrick_points + self.penalty_points

class Score:
    def __init__(self, team_ns_name:str = 'team_NS', team_ew_name:str = 'team_ew'):
        self.team_ns = TeamScore(team_ns_name)
        self.team_ew = TeamScore(team_ew_name)
        self.games = ['game 1', 'game 2', 'game 3']
        self.curr_game_index = 0

    def __str__(self):
        # Table header
        header = (
            f"{'Team Name':<15} {'Game 1':<10} {'Game 2':<10} {'Game 3':<10} "
            f"{'Rubber':<10} {'Slam':<10} {'Double':<10} {'Overtricks':<10} "
            f"{'Penalty':<10} {'Sum':<10}"
        )

        # Team scores
        team_ns_score = (
            f"{self.team_ns.team_name:<15} {self.team_ns.game_points['game 1']:<10} "
            f"{self.team_ns.game_points['game 2']:<10} {self.team_ns.game_points['game 3']:<10} "
            f"{self.team_ns.rubber_bonus:<10} {self.team_ns.slam_bonus:<10} "
            f"{self.team_ns.double_bonus:<10} {self.team_ns.overtrick_points:<10} "
            f"{self.team_ns.penalty_points:<10} {self.team_ns.score_sum():<10}"
        )

        team_ew_score = (
            f"{self.team_ew.team_name:<15} {self.team_ew.game_points['game 1']:<10} "
            f"{self.team_ew.game_points['game 2']:<10} {self.team_ew.game_points['game 3']:<10} "
            f"{self.team_ew.rubber_bonus:<10} {self.team_ew.slam_bonus:<10} "
            f"{self.team_ew.double_bonus:<10} {self.team_ew.overtrick_points:<10} "
            f"{self.team_ew.penalty_points:<10} {self.team_ew.score_sum():<10}"
        )

        return f"{header}\n{team_ns_score}\n{team_ew_score}"

    def update_game_score(self, contract: BridgeContract, tricks_ns: int, tricks_ew: int) -> bool:
        if contract.declarer in [Direction.NORTH, Direction.SOUTH]:
            team_to_update = self.team_ns
            tricks = tricks_ns
        else:
            team_to_update = self.team_ew
            tricks = tricks_ew

        game_status = team_to_update.update_score(contract.level, contract.suit, contract.doubled, tricks, self.games[self.curr_game_index])

        if game_status == 'Game finished':
            self.curr_game_index += 1
        if game_status == 'Rubber finished':
            return True
        return False