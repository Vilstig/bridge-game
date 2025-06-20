from random import shuffle
from typing import Optional

from core.deal_enums import GameStatus, Direction, Suit
from game_logic import Game


class Cli:
    def __init__(self):
        self.rubber = Game()
        self.current_status = None
        self.visible_hand = None

    def game_loop(self):
        while self.current_status != GameStatus.GAME_OVER:
            self.print_header()
            self.choose_action()

    def print_header(self):
        rubber_status = self.rubber.game_status
        if self.current_status != rubber_status:
            if rubber_status == GameStatus.DEAL_CARDS:
                print("Cards are being dealt...")
            elif rubber_status == GameStatus.AUCTION:
                print("\n=== Auction Phase Begins ===")
                print(f"{self.rubber.game_starter_direction} starts auction")
            elif rubber_status == GameStatus.PLAY:
                print("\n=== Auction Phase Finished ===")
                print(f"Contract: {self.rubber.auction.contract}")
                print(f"Declarer: {self.rubber.auction.contract.declarer}, Trump Suit: {self.rubber.play.trump_suit}\n")
                print("\n=== Play Phase Begins ===")
            elif rubber_status == GameStatus.DISPLAY_SCORE:
                print("\n=== Play Phase Finished ===")
                print(f"Final Scores - NS: {self.rubber.play.tricks_ns}, WS: {self.rubber.play.tricks_ew}")
                print(f"Contract: {self.rubber.auction.contract}")
                print(f"Scores:\n{self.rubber.score}")
            elif rubber_status == GameStatus.GAME_OVER:
                print("\nGame over!")
                print(f"Final scores:\n{self.rubber.score}")
                print("Thanks for playing")

            self.current_status = rubber_status

    def choose_action(self):
        if self.rubber.game_status == GameStatus.DEAL_CARDS:
            self.rubber.deal_cards()

        elif self.rubber.game_status == GameStatus.AUCTION:
            current_player = get_player_by_direction(self.rubber.players, self.rubber.playing_direction)
            print(f"\nPlayer: {current_player.name} bids")
            print(f"Current contract: {self.rubber.auction.contract}")
            print(f"Player's hand: {current_player.hand}")
            bid = input(f'Make a bid: ').strip()
            self.rubber.bid(bid)

        elif self.rubber.game_status == GameStatus.PLAY:
            curr_trick = self.rubber.play.trick
            if not curr_trick:
                print("\n--- New Trick ---")
                print(f"Tricks NS: {self.rubber.play.tricks_ns}, Tricks WS: {self.rubber.play.tricks_ew}")

            current_player = get_player_by_direction(self.rubber.players, self.rubber.playing_direction)
            print(f"\nPlayer {current_player.name} ({current_player.direction})'s turn.")
            if curr_trick:
                print(f"Current trick so far: {', '.join([f'{direction}: {card}' for direction, card in curr_trick])}")
            else:
                print("Starting a new trick.")
            print_table(self.rubber.players, self.visible_hand, current_player.direction)
            self.visible_hand = self.rubber.auction.contract.declarer.partner()  # This should be updated once after the first trick, but I don't want to think too much, it's too late
            #card_str = input('Play a card: ').strip().upper()
            card_str = play_random_card(current_player, self.rubber.play.trick[0][1].suit if self.rubber.play.trick else None)  #testing
            self.rubber.play_card(card_str)

            if not self.rubber.play.trick:
                finished_trick = self.rubber.play.tricks_log[self.rubber.play.tricks_ew + self.rubber.play.tricks_ns - 1]
                print("\nTrick completed.")
                print("Trick summary:")
                for player_direction, card in finished_trick:
                    print(f"{player_direction}: {card}")

        elif self.rubber.game_status == GameStatus.DISPLAY_SCORE:
            self.rubber.prepare_new_deal()



def get_player_by_direction(players, direction):
    for player in players:
        if player.direction == direction:
            return player
    raise ValueError("Invalid direction")


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
        if current_direction == visible_hand_direction:
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


def play_random_card(player, led_suit: Optional[Suit]) -> str:  #for testing purpose
    # Sprawdzanie, czy gracz ma karty w ręce
    if not player.hand.cards:
        raise ValueError("Player has no cards left in hand.")

    viable_cards = []

    # Wybieranie kart w kolorze wywołanej karty
    if led_suit:
        for card in player.hand.cards:
            if card.suit == led_suit:
                viable_cards.append(str(card))

    # Jeśli brak kart w kolorze wywołanej karty, dodaj wszystkie karty do puli
    if len(viable_cards) == 0:
        for card in player.hand.cards:
            viable_cards.append(str(card))

    # Ostateczna weryfikacja, czy można coś zagrać
    if not viable_cards:
        raise ValueError('No viable cards to choose from')

    shuffle(viable_cards)
    return viable_cards[0]

if __name__ == "__main__":
    cli = Cli()
    cli.game_loop()