from copy import copy
from random import shuffle
from typing import List, Optional

import core
from core import Card, BridgeContract
from core.deal_enums import SpecialBid, Direction, Suit
from core.play_utils import validate_card_usage, evaluate_trick_winner, Score


class Player:
    def __init__(self, name: str, cards: Optional[List[Card]], direction: str) -> None:
        self.name = name
        self.direction = core.Direction.from_str(direction)
        if cards:
            self.hand = core.PlayerHand.from_cards(cards)

    def play_card(self) -> Card:
        if not self.hand.cards:
            raise ValueError("Player has no cards left in hand.")

        card_str = input('Play a card: ').strip()

        try:
            played_card = Card.from_str(card_str)
        except Exception:
            raise f"Invalid card input: '{card_str}'. Please try again."
        else:
            if played_card not in self.hand.cards:
                raise f"The card '{played_card}' is not in your hand."
            else:
                self.hand.cards.remove(played_card)
                return played_card


    def play_random_card(self, led_suit: Suit) -> Card:
        # Sprawdzanie, czy gracz ma karty w ręce
        if not self.hand.cards:
            raise ValueError("Player has no cards left in hand.")

        viable_cards = []

        # Wybieranie kart w kolorze wywołanej karty
        if led_suit:
            for card in self.hand.cards:
                if card.suit == led_suit:
                    viable_cards.append(card)

        # Jeśli brak kart w kolorze wywołanej karty, dodaj wszystkie karty do puli
        if len(viable_cards) == 0:
            viable_cards.extend(self.hand.cards)

        # Ostateczna weryfikacja, czy można coś zagrać
        if not viable_cards:
            raise ValueError('No viable cards to choose from')

        shuffle(viable_cards)
        return viable_cards[0]


def _deal_cards(players: List[Player]) -> None:
    all_cards = [core.Card(suit, rank) for suit in core.Suit for rank in core.Rank]
    shuffle(all_cards)
    index = 0
    for player in players:
        player.hand = core.PlayerHand.from_cards(all_cards[index:index+13])
        index += 13


class Game:
    def __init__(self):
        self.players = []
        self._init_players()
        self.contract = core.BridgeContract.empty_contract()
        self.contract_log = []
        self.score = Score()
        self.game_over = False

    def _init_players(self):
        player1 = Player('Filip', None, 'N')
        player2 = Player('Dorota', None, 'E')
        player3 = Player('Tomek', None, 'S')
        player4 = Player('Adam', None, 'W')

        self.players = [player1, player2, player3, player4]

    def game_loop(self):
        print("Welcome to bridge game")
        print("Let the suffering begin...\n\n")

        while not self.game_over:
            _deal_cards(self.players)
            self.auction()
            self.play()
            print("\n")

        print("Game over!")
        print(f"Final scores:\n{self.score}")
        print("Thanks for playing")

    def auction(self):
        pass_count = 0
        curr_bid = None
        curr_index = 0
        self.contract = core.BridgeContract.empty_contract()
        self.contract_log = []

        while True:
            current_player = self.players[curr_index]
            print(f"Player: {current_player.name} bids")
            print(f"Current bid: {self.contract}")
            print(f"Player's hand: {current_player.hand}")
            bid = input(f'Make a bid: ').strip()
            new_bid = core.BridgeBid.from_str(bid)

            if new_bid.special == SpecialBid.PASS:
                pass_count += 1

            elif new_bid.verify_legality(previous_bid=curr_bid, new_bid_direction=current_player.direction,
                                         contract_direction=self.contract.declarer):
                curr_bid = new_bid
                self.contract.update_from_bridge_bid(curr_bid, current_player.direction)
                self.contract_log.append(copy(self.contract))
                pass_count = 0
            else:
                print('Invalid bid')

            if pass_count == 4:
                print('Passed out')
                break

            elif curr_bid and pass_count == 3:
                print(f'\nContract: {self.contract}\n')
                break

            curr_index = (curr_index + 1) % 4


    def play(self):
        tricks_ns = 0
        tricks_ew = 0
        trump_suit = self.contract.suit
        starting_player_direction = determine_game_starting_player(self.contract_log)
        visible_hand_direction = None
        trick_starting_player = starting_player_direction

        print("\n=== Play Phase Begins ===")
        print(f"Contract: {self.contract}")
        print(f"Declarer: {self.contract.declarer}, Trump Suit: {trump_suit}\n")

        while tricks_ns + tricks_ew < 13:
            trick = []

            print("\n--- New Trick ---")
            print(f"Tricks NS: {tricks_ns}, Tricks WS: {tricks_ew}")
            
            while len(trick) < 4:
                current_player = select_player(trick_starting_player, self.players)
                
                print(f"\nPlayer {current_player.name} ({current_player.direction})'s turn.")
                if trick:
                    print(f"Current trick so far: {', '.join([f'{direction}: {card}' for direction, card in trick])}")
                else:
                    print("Starting a new trick.")
                print_table(self.players, visible_hand_direction, current_player.direction)
                print(f"Player {current_player.name} ({current_player.direction}) to play.")

                valid = False
                played_card = None

                while not valid:
                    played_card = current_player.play_random_card(trick[0][1].suit if trick else None) #Change this to play_card() to be able to play manually
                    if not validate_card_usage(played_card, trick, current_player.hand):
                            print(f"The card '{played_card}' cannot legally be played.")
                    else:
                        valid = True  # Wszystko OK, karta poprawna


                trick.append((current_player.direction, played_card))
                trick_starting_player = trick_starting_player.next()

                if tricks_ns + tricks_ew == 0 and len(trick) == 1:  #show playing player's partner's cards after first played card
                    visible_hand_direction = self.contract.declarer.partner()

            print("\nTrick completed.")
            print("Trick summary:")
            for player_direction, card in trick:
                print(f"{player_direction}: {card}")

            winner = evaluate_trick_winner(trick, trump_suit)
            print(f"Trick winner: {winner}")

            trick_starting_player = select_player_by_winner(trick, winner)
            if trick_starting_player in [Direction.NORTH, Direction.SOUTH]:
                tricks_ns += 1
            else:
                tricks_ew += 1

        print("\n=== Play Phase Finished ===")
        print(f"Final Scores - NS: {tricks_ns}, WS: {tricks_ew}")
        print(f"Contract: {self.contract}")
        self.game_over = self.score.update_game_score(self.contract, tricks_ns, tricks_ew)
        print(f"Scores:\n{self.score}")

def select_player(direction, players):
    for player in players:
        if player.direction == direction:
            return player

    return None

def select_player_by_winner(trick, winner):
    for direction, card in trick:
        if winner == card:
            return direction
    return None

def print_table(players, visible_hand_direction, current_direction):
    player_map = {p.direction: p for p in players}

    def format_hand(hand, visible):
        suits = {Suit.SPADES: [], Suit.HEARTS: [], Suit.DIAMONDS: [], Suit.CLUBS: []}
        if visible:
            for card in hand.cards:
                suits[card.suit].append(card.rank.abbreviation())
        # If not visible, leave suits empty (but show suit headings later)
        return suits

    def is_visible(direction):
        if current_direction== visible_hand_direction:
            return direction in [visible_hand_direction, visible_hand_direction.partner()]
        else:
            return direction in [visible_hand_direction, current_direction]

    # Prepare hands
    north = format_hand(player_map[Direction.NORTH].hand, is_visible(Direction.NORTH))
    south = format_hand(player_map[Direction.SOUTH].hand, is_visible(Direction.SOUTH))
    west = format_hand(player_map[Direction.WEST].hand, is_visible(Direction.WEST))
    east = format_hand(player_map[Direction.EAST].hand, is_visible(Direction.EAST))

    east_column_start = 65

    # NORTH
    print("\n" + " " * 30 + f"{player_map[Direction.NORTH].name} (N)")
    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        cards = ' '.join(north[suit])
        print(" " * 30 + f"{suit} {cards}")
    print()

    # WEST and EAST headers
    west_name = f"{player_map[Direction.WEST].name} (W)"
    east_name = f"{player_map[Direction.EAST].name} (E)"
    print(f"{west_name:<25}{' ' * (east_column_start - 25)}{east_name}")

    # WEST and EAST hands
    def line(suit, west_suit, east_suit):
        west_line = f"{suit} {' '.join(west_suit)}"
        east_line = f"{suit} {' '.join(east_suit)}"
        return f"{west_line:<{east_column_start}}{east_line}"

    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        print(line(suit, west[suit], east[suit]))
    print()

    # SOUTH
    print(" " * 30 + f"{player_map[Direction.SOUTH].name} (S)")
    for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
        cards = ' '.join(south[suit])
        print(" " * 30 + f"{suit} {cards}")
    print()

def determine_game_starting_player(contract_log: List[BridgeContract]):
    final_contract = contract_log[-1]
    for contract in contract_log:
        if contract.suit == final_contract.suit:
            if contract.declarer == final_contract.declarer.partner():
                return contract.declarer.next()
            elif contract.declarer == final_contract.declarer:
                return contract.declarer.next()
    return final_contract.declarer.next()



game = Game()
game.game_loop()