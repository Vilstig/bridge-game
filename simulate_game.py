from random import shuffle
import core
from core import Card
from core.deal_enums import SpecialBid, Direction, Suit
from core.play_utils import validate_card_usage, evaluate_trick_winner


class Player:
    def __init__(self, name: str, cards, direction: str) -> None:
        self.name = name
        self.hand = core.PlayerHand.from_cards(cards)
        self.direction = core.Direction.from_str(direction)

class Game:
    def __init__(self):
        self.players = []
        self._init_players()
        self.contract = core.BridgeContract.empty_contract()


    def _init_players(self):
        all_cards = [core.Card(suit, rank) for suit in core.Suit for rank in core.Rank]
        shuffle(all_cards)

        player1 = Player('Filip', all_cards[:13], 'N')
        player2 = Player('Dorota', all_cards[13:26], 'E')
        player3 = Player('Tomek', all_cards[26:39], 'S')
        player4 = Player('Adam', all_cards[39:], 'W')

        self.players = [player1, player2, player3, player4]

    def auction(self):
        pass_count = 0
        curr_bid = None
        curr_index = 0

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
        tricks_NS = 0
        tricks_WS = 0
        trump_suit = self.contract.suit
        starting_player_direction = self.contract.declarer.next()
        visible_hand_direction = self.contract.declarer.partner()

        print("\n=== Play Phase Begins ===")
        print(f"Contract: {self.contract}")
        print(f"Declarer: {self.contract.declarer}, Trump Suit: {trump_suit}\n")

        while tricks_NS + tricks_WS < 13:
            trick = []

            print("\n--- New Trick ---")
            print(f"Tricks NS: {tricks_NS}, Tricks WS: {tricks_WS}")
            
            while len(trick) < 4:
                current_player = select_player(starting_player_direction, self.players)
                
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
                    card_str = input('Play a card: ').strip()

                    try:
                        played_card = Card.from_str(card_str)
                    except Exception:
                        print(f"Invalid card input: '{card_str}'. Please try again.")
                    else:
                        if played_card not in current_player.hand.cards:
                            print(f"The card '{played_card}' is not in your hand.")
                        elif not validate_card_usage(played_card, trick, current_player.hand):
                            print(f"The card '{played_card}' cannot legally be played.")
                        else:
                            valid = True  # Wszystko OK, karta poprawna
                            current_player.hand.cards.remove(played_card)
                            print(f"Card played: {played_card}")

                trick.append((current_player.direction, played_card))
                starting_player_direction = starting_player_direction.next()

            print("\nTrick completed.")
            print("Trick summary:")
            for player_direction, card in trick:
                print(f"{player_direction}: {card}")

            winner = evaluate_trick_winner(trick, trump_suit)
            print(f"Trick winner: {winner}")

            starting_player_direction = select_player_by_winner(trick, winner)
            if starting_player_direction in [Direction.NORTH, Direction.SOUTH]:
                tricks_NS += 1
            else:
                tricks_WS += 1

        print("\n=== Play Phase Finished ===")
        print(f"Final Scores - NS: {tricks_NS}, WS: {tricks_WS}")

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





game = Game()
game.auction()
game.play()