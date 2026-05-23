from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db, init_db

DEFAULT_PLAYERS = ['Silvia', 'Giulia', 'Martina']
DEFAULT_RULES = [
    ('Drink offerto', 3),
    ('Numero o Instagram richiesto', 1),
    ('Sfida bonus completata', 5),
    ('Missione speciale completata', 10),
    ('Penalità decisa dal giudice', -5),
]

app = create_app()
with app.app_context():
    init_db()
    db = get_db()
    demo_hash = generate_password_hash('demo123')
    for name in DEFAULT_PLAYERS:
        uname = name.lower().replace(' ', '_')
        exists = db.execute(
            'SELECT id FROM players WHERE username = ? OR name = ?',
            (uname, name),
        ).fetchone()
        if not exists:
            db.execute(
                'INSERT INTO players (name, username, password_hash) VALUES (?, ?, ?)',
                (name, uname, demo_hash),
            )
    for title, points in DEFAULT_RULES:
        existing = db.execute('SELECT id FROM rules WHERE title = ?', (title,)).fetchone()
        if not existing:
            db.execute('INSERT INTO rules (title, points) VALUES (?, ?)', (title, points))
    db.commit()
    print('Database inizializzato con dati demo (login giocatori: username silvia / giulia / martina, password demo123).')
