from core.deal_enums import GameStatus, Direction
from game_logic import Game, get_player_by_direction

class Handler:
    def __init__(self):
        self.rubber = Game()
        self.visible_hand = None
        self.player_dict = {}  # sid: {dir: ..., ready:..., has_played:...}
        self.game_running = False

    def get_game_status_str(self) -> str:
        return str(self.rubber.game_status)

    def available_dirs(self):
        return [d.abbreviation() for d in Direction if d not in self.rubber.taken_dirs()]

    def add_player(self, sid, role: str) -> bool:
        if Direction.from_str(role[0]) in self.rubber.taken_dirs():
            return False
        player = get_player_by_direction(self.rubber.players, Direction.from_str(role))
        player.name = 'Prr Prr Patapim'
        self.player_dict[sid] = {'dir': role[0], 'ready': False, 'has_played': False}
        return True

    def get_status(self):
        return {
            'players': {p['dir']: p['ready'] for p in self.player_dict.values()},
            'game_running': self.game_running
        }

    def get_player_hands(self):
        return {
            sid: [str(card) for card in get_player_by_direction(self.rubber.players, Direction.from_str(info['dir'])).hand.cards]
            for sid, info in self.player_dict.items()
        }

    def get_direction_hands(self):
        return {
            player.direction.abbreviation(): [str(card) for card in player.hand.cards]
            for player in self.rubber.players
        }

    def auction_status(self):
        rounds, dir_names = self.rubber.get_bidding_history()
        return {
            'turn': self.rubber.playing_direction.abbreviation(),
            'contract': str(self.rubber.auction.contract),
            'hands': self.get_player_hands(),
            'bids': self.rubber.get_legal_bids(),
            'player_turns': self.player_turns(),
            'direction_hands': self.get_direction_hands(),
            'bidding_history': [rounds, dir_names],
        }

    def player_turns(self):
        return {
            sid: self.player_dict[sid]['dir'] == self.rubber.playing_direction.abbreviation()
            for sid in self.player_dict
        }

    def toggle_ready(self, sid):
        if sid in self.player_dict:
            self.player_dict[sid]['ready'] = not self.player_dict[sid]['ready']
            if len(self.player_dict) == 4 and all(p['ready'] for p in self.player_dict.values()):
                self.game_running = True

    def remove_player(self, sid) -> bool:
        if sid in self.player_dict:
            player = get_player_by_direction(self.rubber.players, Direction.from_str(self.player_dict[sid]['dir']))
            player.name = ''
            self.player_dict.pop(sid)
            self.game_running = False
            for p in self.player_dict.values():
                p['ready'] = False
            return True
        return False

    def deal_cards(self) -> bool:
        if self.valid_status(GameStatus.DEAL_CARDS):
            self.rubber.deal_cards()
            return True
        return False

    def valid_status(self, exp_status: GameStatus) -> bool:
        return self.rubber.game_status == exp_status

    def make_bid(self, sid, bid) -> bool:
        if not self.valid_status(GameStatus.AUCTION) or self.player_dict[sid]['dir'] != self.rubber.playing_direction.abbreviation():
            return False
        self.rubber.bid(bid)
        if self.valid_status(GameStatus.DEAL_CARDS):
            self.deal_cards()
        return True

    def play_status(self):
        trick = self.rubber.get_current_trick()
        return {
            'turn': self.rubber.playing_direction.abbreviation(),
            'trick_count': self.rubber.get_tricks_count(),
            'trick': [(d.abbreviation(), str(c)) for d, c in trick],
            'last_full_trick': [(d.abbreviation(), str(c)) for d, c in self.rubber.play.tricks_log[-1]] if self.rubber.play.tricks_log else [],
            'direction_hands': self.get_direction_hands()
        }

    def player_hand_update(self):
        return {
            'legal_hand': [str(card) for card in self.rubber.get_legal_cards_to_play()],
            'player_turns': self.player_turns()
        }

    def play_card(self, card: str):
        self.rubber.play_card(card)

    def score_status(self):
        return {
            'trick_count': self.rubber.get_tricks_count(),
            'contract': str(self.rubber.get_contract()),
            'scores': str(self.rubber.get_current_scores())
        }

    def end_scores(self):
        self.rubber.prepare_new_deal()
        self.rubber.deal_cards()

    def game_over_status(self):
        return {'scores': str(self.rubber.get_current_scores())}

    def get_visible_hands_per_sid(self):
        all_hands = self.get_direction_hands()
        vis_dir = self.rubber.visible_direction
        result = {}

        for sid, pdata in self.player_dict.items():
            my_dir = pdata['dir']
            visible_dirs = {my_dir}
            if vis_dir:
                visible_dirs |= {vis_dir.abbreviation()}

            result[sid] = {
                d: all_hands[d] if d in visible_dirs else ['*'] * len(all_hands[d])
                for d in all_hands
            }

        return result
