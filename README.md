# 🃏 Bridge Game

Aplikacja webowa do rozgrywania brydża dla czterech graczy, stworzona w Pythonie z użyciem Flask, Socket.IO oraz frontendu HTML/CSS/JS.

---

## 📁 Struktura katalogów

```
bridge_game/
├── assets/              # Zasoby graficzne kart (PNG/SVG)
│   ├── PNG-cards/
│   └── SVG-cards/
├── core/                # Logika gry
│   ├── bids.py
│   ├── board_record.py
│   ├── deal.py
│   ├── deal_enums.py
│   ├── play_utils.py
│   └── tests/           # Testy jednostkowe (opcjonalnie)
├── static/              # Pliki statyczne (frontend)
│   ├── assets/          # Obrazy (np. card_back.png)
│   ├── client.js        # Logika klienta Socket.IO
│   └── style.css        # Styl CSS gry
├── templates/
│   ├── game.html        # Główna strona gry (Jinja2)
│   ├── client.js        # Główna strona gry (JS)
├── app.py               # Tryb HTTP (klasyczny)
├── app_socket.py        # Tryb realtime (Socket.IO)
├── cli_interface.py     # Wersja konsolowa gry
├── game_handler.py      # Obsługa logiki gry (SocketIO)
├── game_logic.py        # Główna logika gry
├── .gitignore
├── LICENSE              # Licencja MIT
└── todo.txt             # Notatki developerskie
```

---

## 🧪 Wymagania

- Python 3.10+
- Przeglądarka z obsługą JS/WebSocket

### Instalacja zależności

Utwórz i zainstaluj zależności z pliku `requirements.txt`:



Instalacja:

```bash
pip install -r requirements.txt
```

---

## 🚀 Uruchomienie aplikacji

### Tryb realtime (Socket.IO) — rekomendowany:

```bash
python app_socket.py
```

Następnie otwórz przeglądarkę i przejdź do:

```
http://localhost:5000
```

Uruchom cztery zakładki – każda reprezentuje jednego gracza: North, East, South, West.

### Tryb klasyczny (HTTP):

```bash
python app.py
```

Ten tryb wykorzystuje Jinja2 do dynamicznego renderowania HTML przy każdej akcji.

---

## 🧠 Jak działa gra?

1. Gracze wybierają kierunki i oznaczają gotowość.
2. Gra automatycznie przechodzi przez:
   - Licytację zgodną z zasadami brydża
   - Rozdanie kart
   - Zagrywanie tricków
   - Liczenie punktów i bonusów
3. Na końcu rubbera prezentowana jest tabela wyników.

---

## 📊 Główne funkcje

- Pełna obsługa licytacji brydżowej
- Rozpoznawanie deklarującego i wistującego
- Wyświetlanie tricków i kart na stole
- Liczenie punktów, bonusów, nadbić i rubberów
- Graficzna reprezentacja stołu i kart (obracanie, rewersy)
- Tryb webowy w czasie rzeczywistym z Socket.IO
- Konsolowa wersja gry (CLI)

---

## ✅ Sterowanie

- Aktywna karta tylko dla aktualnego gracza
- Licytacja poprzez kliknięcie lub wybór z listy
- Przycisk „Next phase” inicjuje nowe rozdanie

---


## 🧾 Licencja

Projekt objęty jest licencją **MIT**. Szczegóły znajdują się w pliku `LICENSE`.

---


Miłej gry! 🎴