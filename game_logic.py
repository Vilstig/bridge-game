from copy import copy
from random import shuffle
from typing import List, Optional

import core
from core import Card, BiddingSuit
from core.deal_enums import SpecialBid, Direction, GameStatus
from core.play_utils import validate_card_usage, evaluate_trick_winner, Score


class Player:
    def __init__(self, name: str, cards: Optional[List[Card]], direction: str) -> None:
        self.name = name
        self.direction = core.Direction.from_str(direction)
        if cards:
            self.hand = core.PlayerHand.from_cards(cards)

    def play_card(self, card: str) -> Card:
        if not self.hand.cards:
            raise ValueError("Player has no cards left in hand.")

        try:
            played_card = Card.from_str(card)
        except Exception:
            raise f"Invalid card input: '{card}'."
        else:
            if played_card not in self.hand.cards:
                raise f"The card '{played_card}' is not in your hand."
            else:
                self.hand.cards.remove(played_card)
                return played_card


class Game:
    def __init__(self):
        self.players = []
        self._init_players()
        self.auction = Auction()
        self.play = None
        self.score = Score()
        self.game_status = GameStatus.DEAL_CARDS  # 'Deal cards', 'Auction', 'Play, 'Display score', 'Game over'
        self.game_starter_direction = Direction.NORTH
        self.playing_direction = None

    def _init_players(self):
        player1 = Player('Filip', None, 'N')
        player2 = Player('Dorota', None, 'E')
        player3 = Player('Tomek', None, 'S')
        player4 = Player('Adam', None, 'W')

        self.players = [player1, player2, player3, player4]

    def deal_cards(self) -> None:
        if self.game_status != GameStatus.DEAL_CARDS:
            raise ValueError(f"Game status must be 'Deal cards' to invoke this action")

        all_cards = [core.Card(suit, rank) for suit in core.Suit for rank in core.Rank]
        shuffle(all_cards)
        index = 0

        for player in self.players:
            player.hand = core.PlayerHand.from_cards(all_cards[index:index + 13])
            index += 13

        self.playing_direction = self.game_starter_direction
        self.game_status = GameStatus.AUCTION

    def bid(self, bid: str) -> None:
        if self.game_status != GameStatus.AUCTION:
            raise ValueError(f"Game status must be 'Auction' to invoke this action")

        self.auction.bid(self.playing_direction, bid)
        if self.auction.auction_end():
            if self.auction.pass_count == 4:
                self.prepare_new_deal()
            else:
                self.game_status = GameStatus.PLAY
                self.play = Play(self.auction.contract.suit)
                self.playing_direction = self.auction.determine_play_starting_direction()
        else:
            self.playing_direction = self.playing_direction.next()

    def play_card(self, card: str) -> None:
        if self.game_status != GameStatus.PLAY:
            raise ValueError(f"Game status must be 'Play' to invoke this action")

        current_player = get_player_by_direction(self.players, self.playing_direction)

        played_card = current_player.play_card(card)
        self.play.play_card(played_card, current_player)

        if self.play.trick_over():
            finished_trick = self.play.tricks_log[self.play.tricks_ew + self.play.tricks_ns - 1]
            winner = evaluate_trick_winner(finished_trick, self.play.trump_suit)
            winning_direction = select_player_by_winner(finished_trick, winner)
            if winning_direction in [Direction.NORTH, Direction.SOUTH]:
                self.play.tricks_ns += 1
            else:
                self.play.tricks_ew += 1
            self.playing_direction = winning_direction
            if self.play.play_over():
                game_over = self.score.update_game_score(self.auction.contract, self.play.tricks_ns, self.play.tricks_ew)

                if game_over:
                    self.game_status = GameStatus.GAME_OVER
                else:
                    self.game_status = GameStatus.DISPLAY_SCORE
        else:
            self.playing_direction = self.playing_direction.next()

    def prepare_new_deal(self):
        if self.game_status in [GameStatus.AUCTION, GameStatus.DISPLAY_SCORE]:
            self.game_status = GameStatus.DEAL_CARDS
            self.auction = Auction()
            self.game_starter_direction = self.game_starter_direction.next()


class Auction:
    def __init__(self):
        self.contract = core.BridgeContract.empty_contract()
        self.pass_count = 0
        self.curr_bid = None
        self.contract_log = []

    def bid(self, bidding_player_direction: Direction, bid: str):
        new_bid = core.BridgeBid.from_str(bid)

        if new_bid.special == SpecialBid.PASS:
            self.pass_count += 1

        elif new_bid.verify_legality(previous_bid=self.curr_bid, new_bid_direction=bidding_player_direction,
                                     contract_direction=self.contract.declarer):
            self.curr_bid = new_bid
            self.contract.update_from_bridge_bid(self.curr_bid, bidding_player_direction)
            self.contract_log.append(copy(self.contract))
            self.pass_count = 0
        else:
            raise ValueError('Illegal bid')

    def auction_end(self):
        if self.pass_count == 4:
            return True
        elif self.pass_count == 3 and self.curr_bid is not None:
            return True
        return False

    def determine_play_starting_direction(self) -> Direction:
        final_contract = self.contract_log[-1]
        for contract in self.contract_log:
            if contract.suit == final_contract.suit:
                if contract.declarer == final_contract.declarer.partner():
                    return contract.declarer.next()
                elif contract.declarer == final_contract.declarer:
                    return contract.declarer.next()
        return final_contract.declarer.next()


class Play:
    def __init__(self, trump_suit: BiddingSuit):
        self.tricks_ns = 0
        self.tricks_ew = 0
        self.trump_suit = trump_suit
        self.tricks_log = []
        self.trick = []

    def play_card(self, card: Card, player: Player) -> None:
        if not validate_card_usage(card, self.trick, player.hand):
            raise ValueError(f"The card '{card}' cannot legally be played.")

        if len(self.trick) < 4:
            self.trick.append((player.direction, card))
        else:
            raise ValueError('Trick size equals 4. Cannot append a new card')

    def trick_over(self) -> bool:
        if len(self.trick) < 4:
            return False
        elif len(self.trick) == 4:
            self.tricks_log.append(self.trick)
            self.trick = []
            return True
        else:
            raise ValueError('Trick size exceeded 4')

    def play_over(self) -> bool:
        tricks_sum = self.tricks_ns + self.tricks_ew
        if tricks_sum < 13:
            return False
        elif tricks_sum == 13:
            return True
        else:
            raise ValueError('Tricks sum exceed 13')


def select_player_by_winner(trick, winner):
    for direction, card in trick:
        if winner == card:
            return direction
    return None

def get_player_by_direction(players, direction):
    for player in players:
        if player.direction == direction:
            return player
    raise ValueError("Invalid direction")