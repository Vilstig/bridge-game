from copy import copy
from random import shuffle
from typing import List, Optional

import core
from core import Card, BiddingSuit
from core.bids import LEGAL_BIDS
from core.deal_enums import SpecialBid, Direction, GameStatus
from core.play_utils import validate_card_usage, evaluate_trick_winner, Score, InvalidGameActionError, \
    select_player_by_winner, get_player_by_direction


class Player:
    def __init__(self, name: str, cards: Optional[List[Card]], direction: str) -> None:
        self.name = name
        self.direction = core.Direction.from_str(direction)
        self.hand = core.PlayerHand.from_cards(cards) if cards else None

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
        self.deal_cards()

    def _init_players(self) -> None:
        player1 = Player('Filip', None, 'N')
        player2 = Player('Dorota', None, 'E')
        player3 = Player('Tomek', None, 'S')
        player4 = Player('Adam', None, 'W')

        self.players = [player1, player2, player3, player4]

    def deal_cards(self) -> None:
        self._validate_game_status(GameStatus.DEAL_CARDS)

        all_cards = [core.Card(suit, rank) for suit in core.Suit for rank in core.Rank]
        shuffle(all_cards)
        index = 0

        for player in self.players:
            player.hand = core.PlayerHand.from_cards(all_cards[index:index + 13])
            index += 13

        self.playing_direction = self.game_starter_direction
        self.game_status = GameStatus.AUCTION

    def bid(self, bid: str) -> None:
        self._validate_game_status(GameStatus.AUCTION)

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
        self._validate_game_status(GameStatus.PLAY)

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
                game_over = self.score.update_game_score(self.auction.contract, self.play.tricks_ns,
                                                         self.play.tricks_ew)

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

    def _validate_game_status(self, expected_status: GameStatus) -> None:
        if self.game_status != expected_status:
            raise InvalidGameActionError(
                f"Game status must be '{expected_status}' to invoke this action"
            )

    def get_bidding_history(self):
        dir_order = [self.game_starter_direction.offset(i) for i in range(4)]
        dir_names = [d.name for d in dir_order]

        rounds = []
        row = [""] * 4
        current_index = 0

        for bid_str in self.auction.bid_log:
            col = current_index % 4
            row[col] = bid_str.split(",")[0]
            current_index += 1
            if col == 3:
                rounds.append(row)
                row = [""] * 4

        # If round isn't full yet, add a '?' in correct column
        if any(cell == "" for cell in row):
            row[current_index % 4] = "?"
            rounds.append(row)

        return rounds, dir_names

    def get_legal_bids(self) -> list[str]:
        legal = []
        all_bids = LEGAL_BIDS
        for bid_str in all_bids:
            bid = core.BridgeBid.from_str(bid_str)
            if core.play_utils.is_bid_legal(previous_bid=self.auction.curr_bid, last_contract=self.get_contract(),
                                            new_bid=bid, new_bid_direction=self.playing_direction):
                legal.append(bid_str)

        return legal

    def get_players(self) -> List['Player']:
        """Zwraca listę graczy."""
        return self.players

    def get_game_status(self) -> GameStatus:
        """Zwraca obecny status gry."""
        return self.game_status

    def get_game_starter_direction(self) -> Direction:
        """Zwraca kierunek gracza rozpoczynającego grę."""
        return self.game_starter_direction

    def get_playing_direction(self) -> Direction:
        """Zwraca obecny kierunek gracza, który ma wykonywać ruch."""
        return self.playing_direction

    def get_contract(self) -> core.BridgeContract:
        """Zwraca bieżący kontrakt z aukcji."""
        return self.auction.contract if self.auction else None

    def get_current_scores(self) -> Score:
        """Zwraca aktualny wyniki w grze."""
        return self.score

    def get_current_trick(self) -> Optional[List[tuple]]:
        """Zwraca bieżący trick (o ile taki istnieje)."""
        return self.play.trick if self.play else None

    def get_tricks_count(self) -> tuple:
        """Zwraca liczbę zebranych tricków przez każdą stronę."""
        if self.play:
            return self.play.tricks_ns, self.play.tricks_ew
        return 0, 0


class Auction:
    def __init__(self):
        self.contract = core.BridgeContract.empty_contract()
        self.pass_count = 0
        self.curr_bid = None
        self.bid_log = []
        self.contract_log = []

    def bid(self, bidding_player_direction: Direction, bid: str) -> None:
        new_bid = core.BridgeBid.from_str(bid)

        if new_bid.special == SpecialBid.PASS:
            self.pass_count += 1
            self.bid_log.append('PASS')

        elif core.play_utils.is_bid_legal(previous_bid=self.curr_bid, last_contract=self.contract, new_bid=new_bid,
                                          new_bid_direction=bidding_player_direction):
            self.curr_bid = new_bid
            self.contract.update_from_bridge_bid(self.curr_bid, bidding_player_direction)
            self.bid_log.append(bid)
            self.contract_log.append(copy(self.contract))
            self.pass_count = 0
        else:
            raise ValueError('Illegal bid')

    def auction_end(self) -> bool:
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
