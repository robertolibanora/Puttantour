# Points Game App

Mini web app Flask per un gioco a punti: l'admin/giudice assegna eventi e punti, gli utenti vedono classifica e punteggio.

## Funzioni
- Leaderboard pubblica
- Pagina giocatore con storico punti
- Admin login
- Creazione giocatori
- Regole configurabili con punti positivi/negativi
- Assegnazione rapida punti
- Storico eventi
- SQLite pronto out-of-the-box

## Avvio locale

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
python run.py
```

Apri: http://127.0.0.1:5000

Admin: http://127.0.0.1:5000/admin/login
Password default: `admin123` nel file `.env`.

## Deploy veloce VPS

```bash
cd /var/www/points-game
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
gunicorn -w 2 -b 127.0.0.1:9300 run:app
```

Poi reverse proxy con Caddy verso `127.0.0.1:9300`.

## Struttura

```text
app/
  __init__.py
  db.py
  routes.py
  templates/
  static/css/shared.css
  static/css/user.css
  static/css/admin.css
run.py
seed.py
requirements.txt
.env.example
```
