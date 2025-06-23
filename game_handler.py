from core.deal_enums import GameStatus, Direction, Suit
from game_logic import Game, Player, get_player_by_direction

class Handler:
    def __init__(self):
        self.rubber = Game()
        self.visible_hand = None
        self.player_dict = {} # sid: {dir: ..., ready:..., has_played:...}
        #self.spectators = set()
        self.game_running = False

    def get_game_status_str(self) -> str:
        return self.rubber.game_status.__str__()

    def available_dirs(self):
        roles = [d.abbreviation() for d in Direction if d not in self.rubber.taken_dirs()]
        #roles.append('Spectator')
        return roles

    def add_player(self, sid, role: str) -> bool: #can this be cleanly refactored to handle nonexistent roles? shouldnt happen, but may be good practice
        '''if role == 'Spectator':
            self.spectators.add(sid)
            return True'''
        if Direction.from_str(role[0]) in self.rubber.taken_dirs():
            return False
        else:
            player = get_player_by_direction(self.rubber.players, Direction.from_str(role))
            player.name = 'Prr Prr Patapim'
            self.player_dict[sid] = {'dir': role[0], 'ready': False, 'has_played': False}
        return True

    def get_status(self):
        return {
            'players': {p['dir']: p['ready'] for p in self.player_dict.values()},
            #'spec_count': len(self.spectators),
            'game_running': self.game_running
        }

    def get_player_hands(self):
        player_ids ={sid: get_player_by_direction(self.rubber.players, Direction.from_str(self.player_dict[sid]['dir'])) for sid in self.player_dict}
        return {sid: player_ids[sid].hand.__repr__() for sid in player_ids}

    def auction_status(self, direction=None):
        return {'turn': self.rubber.playing_direction.abbreviation(),
                'contract': self.rubber.auction.contract.__str__(),
                'hands': self.get_player_hands(),
                'bids': self.rubber.get_legal_bids(),
                'player_turns': self.player_turns()}

    def player_turns(self):
        return {sid: self.player_dict[sid]['dir'] == self.rubber.playing_direction.abbreviation() for sid in self.player_dict}

    def toggle_ready(self, sid):
        if sid in self.player_dict:
            self.player_dict[sid]['ready'] = not self.player_dict[sid]['ready']
            if len(self.player_dict) == 4 and all([p['ready'] for p in self.player_dict.values()]):
                self.game_running = True

    def remove_player(self, sid) -> bool: #dummy players in game instead of deleting them, delete from dict in handler
        if sid in self.player_dict:
            player = get_player_by_direction(self.rubber.players, Direction.from_str(self.player_dict[sid]['dir']))
            player.name = ''
            self.player_dict.pop(sid)
            self.game_running = False
            for p in self.player_dict.values():
                p['ready'] = False
            return True
        #self.spectators.discard(sid)
        return False

    def deal_cards(self) -> bool:
        if self.valid_status(GameStatus.DEAL_CARDS): #should this check be deleted? not necessary, probably never useful, redundancy in make_bid
            self.rubber.deal_cards()
            return True
        return False

    def valid_status(self, exp_status: GameStatus) -> bool:
        return self.rubber.game_status == exp_status

    def make_bid(self, sid, bid) -> bool:
        if not self.valid_status(GameStatus.AUCTION) or self.player_dict[sid]['dir'] != self.rubber.playing_direction.abbreviation():
            return False
        self.rubber.bid(bid)
        if self.valid_status(GameStatus.DEAL_CARDS): #in case of 4 passes in a row at the start
            self.deal_cards()
        return True

    def play_status(self):
        def trick_str() -> str:
            trick = self.rubber.get_current_trick()
            trick_str = ' | '.join([f'{direction.abbreviation()}: {str(card)}' for (direction, card) in trick])
            return trick_str
        turn = self.rubber.playing_direction.abbreviation()
        trick_count = self.rubber.get_tricks_count()
        return {
            'turn': turn,
            'trick_count': trick_count,
            'trick_str': trick_str(),
            'player_views': self.player_hands_str()['player_views']
        }

    def player_hand_update(self):
        return {
            'legal_hand': self.rubber.get_legal_cards_to_play(),
            'player_turns': self.player_turns()
        }

    def player_hands_str(self):
        player_hands = self.get_player_hands()
        vis_dir = self.rubber.playing_direction.abbreviation()
        vis_partner_dir = self.rubber.playing_direction.partner().abbreviation()
        vis_sid = ''
        vis_partner_sid = ''
        for sid in self.player_dict:
            if self.player_dict[sid]['dir'] == vis_dir:
                vis_sid = sid
            elif self.player_dict[sid]['dir'] == vis_partner_dir:
                vis_partner_sid = sid

        player_views = {}
        for sid in self.player_dict:
            card_str = f'Visible hands\n{self.player_dict[sid]["dir"]}: {player_hands[sid]}\n'
            if sid == vis_sid:
                card_str += f'{vis_partner_dir}: {player_hands[vis_partner_sid]}'
            else:
                card_str += f'{vis_dir}: {player_hands[vis_sid]}'
            player_views[sid] = card_str


        return{
            'hands': player_hands,
            'vis_sid': vis_sid,
            'vis_partner_sid': vis_partner_sid,
            'player_views': player_views
        }

    def play_card(self, card: str):
        self.rubber.play_card(card)