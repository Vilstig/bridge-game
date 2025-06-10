from random import shuffle
import core
from core.deal_enums import SpecialBid


class Player:
    def __init__(self, name: str, cards, direction: str) -> None:
        self.name = name
        self.hand = core.PlayerHand.from_cards(cards)
        self.direction = core.Direction.from_str(direction)


def simulate_game():
    all_cards = [core.Card(suit, rank) for suit in core.Suit for rank in core.Rank]
    shuffle(all_cards)

    player1 = Player('Filip', all_cards[:13], 'N')
    player2 = Player('Dorota', all_cards[13:26], 'E')
    player3 = Player('Tomek', all_cards[26:39], 'S')
    player4 = Player('Adam', all_cards[39:], 'W')

    players = [player1, player2, player3, player4]

    pass_count = 0
    curr_bid = None
    curr_index = 0
    contract = core.BridgeContract.empty_contract()

    while True:
        current_player = players[curr_index]
        print(f"Player: {current_player.name} bids")
        print(f"Current bid: {contract}")
        print(f"Player's hand: {current_player.hand}")
        bid = input(f'Make a bid: ').strip()
        new_bid = core.BridgeBid.from_str(bid)

        if new_bid.special == SpecialBid.PASS:
            pass_count += 1

        elif new_bid.verify_legality(previous_bid=curr_bid, new_bid_direction=current_player.direction,
                                     contract_direction=contract.declarer):
            curr_bid = new_bid
            contract.update_from_bridge_bid(curr_bid, current_player.direction)
            pass_count = 0
        else:
            print('Invalid bid')

        if pass_count == 4:
            print('Passed out')
            break

        elif curr_bid and pass_count == 3:
            print(f'Contract: {contract}')
            break

        curr_index = (curr_index + 1) % 4

simulate_game()