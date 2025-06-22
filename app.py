from flask import Flask, render_template, request, redirect, url_for
from game_logic import Game

app = Flask(__name__)
game = Game()


@app.route('/')
def index():
    """Strona główna gry."""
    # Sprawdź, czy gracze mają już rozdane karty
    if not all(player.hand for player in game.players):
        hands = None  # Brak rąk do wyświetlenia
    else:
        # Ręce graczy w formacie do szablonu (np. ['2H', '3D', ...])
        hands = {
            direction: [str(card) for card in player.hand.cards]
            for direction, player in zip(['N', 'E', 'S', 'W'], game.players)
        }

    # Trick jako lista [(direction, card), ...], jeśli już rozpoczęto fazę gry
    trick = (
        [(direction.abbreviation(), str(card)) for direction, card in game.play.trick]
        if game.play and game.play.trick else []
    )

    bidding_rounds, bidding_order = game.get_bidding_history()
    legal_bids = game.get_legal_bids()

    return render_template("game.html",
                           game=game,
                           hands=hands,
                           trick=trick,
                           bidding_rounds=bidding_rounds,
                           bidding_order=bidding_order,
                           legal_bids=legal_bids
                           )


@app.route('/deal', methods=['POST'])
def deal():
    """Rozdanie kart."""
    game.deal_cards()
    return redirect(url_for('index'))


@app.route('/bid', methods=['POST'])
def bid():
    """Obsługa licytacji."""
    bid = request.form.get('bid')
    game.bid(bid)
    return redirect(url_for('index'))


@app.route('/play', methods=['POST'])
def play():
    card = request.form.get('card')
    game.play_card(card)
    return redirect(url_for('index'))



@app.route('/next_phase', methods=['POST'])
def next_phase():
    """Przejście do kolejnej fazy."""
    game.prepare_new_deal()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
