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

## PWA (Progressive Web App)

L'app è installabile come PWA su mobile e desktop:

- **Manifest** dinamico con nome app, icone e scorciatoie
- **Service worker** con cache degli asset statici e pagina offline
- **Install prompt** e banner di aggiornamento in-app
- **Safe area** per notch e modalità standalone

Per test locale: avvia con HTTPS (o `localhost`) e usa Chrome DevTools → Application → Manifest / Service Workers.

Per rigenerare le icone dopo aver aggiornato `logo.png` in root:

```bash
pip install Pillow
python scripts/generate_icons.py
```

In produzione servi l'app dietro HTTPS (obbligatorio per installazione su dispositivi reali).

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
