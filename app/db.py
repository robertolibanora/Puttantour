import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def _migrate_players(db):
    info = db.execute('PRAGMA table_info(players)').fetchall()
    colnames = {row[1] for row in info}
    if 'username' not in colnames:
        db.execute('ALTER TABLE players ADD COLUMN username TEXT')
    if 'password_hash' not in colnames:
        db.execute('ALTER TABLE players ADD COLUMN password_hash TEXT')
    if 'disqualified' not in colnames:
        db.execute('ALTER TABLE players ADD COLUMN disqualified INTEGER DEFAULT 0')
    if 'avatar_emoji' not in colnames:
        db.execute('ALTER TABLE players ADD COLUMN avatar_emoji TEXT')
    if 'avatar_bg' not in colnames:
        db.execute('ALTER TABLE players ADD COLUMN avatar_bg TEXT')
    db.execute(
        'CREATE UNIQUE INDEX IF NOT EXISTS idx_players_username '
        'ON players(username) WHERE username IS NOT NULL'
    )


def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        username TEXT,
        password_hash TEXT,
        avatar_emoji TEXT,
        avatar_bg TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        points INTEGER NOT NULL,
        active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS score_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        rule_id INTEGER,
        points INTEGER NOT NULL,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(player_id) REFERENCES players(id),
        FOREIGN KEY(rule_id) REFERENCES rules(id)
    );
    ''')
    _migrate_players(db)
    _migrate_score_events(db)
    db.commit()


def _migrate_score_events(db):
    info = db.execute('PRAGMA table_info(score_events)').fetchall()
    colnames = {row[1] for row in info}
    if 'judge_username' not in colnames:
        db.execute('ALTER TABLE score_events ADD COLUMN judge_username TEXT')


def active_rules():
    return get_db().execute(
        'SELECT * FROM rules WHERE active = 1 ORDER BY points DESC, title ASC',
    ).fetchall()


def recent_score_events(*, limit=5):
    return get_db().execute('''
        SELECT e.*, p.name AS player_name, r.title AS rule_title
        FROM score_events e
        JOIN players p ON p.id = e.player_id
        LEFT JOIN rules r ON r.id = e.rule_id
        ORDER BY e.created_at DESC, e.id DESC
        LIMIT ?
    ''', (limit,)).fetchall()


def player_totals(*, include_disqualified=True):
    where = '' if include_disqualified else 'WHERE COALESCE(p.disqualified, 0) = 0'
    return get_db().execute(f'''
        SELECT p.id, p.name, COALESCE(p.disqualified, 0) AS disqualified,
               p.avatar_emoji, p.avatar_bg,
               COALESCE(SUM(e.points), 0) AS total_points,
               COUNT(e.id) AS events_count
        FROM players p
        LEFT JOIN score_events e ON e.player_id = p.id
        {where}
        GROUP BY p.id, p.name, p.disqualified, p.avatar_emoji, p.avatar_bg
        ORDER BY COALESCE(p.disqualified, 0) ASC,
                 total_points DESC, events_count DESC, p.name ASC
    ''').fetchall()


def resolve_database_path(project_root: Path, configured: str) -> Path:
    path = Path(configured)
    if not path.is_absolute():
        path = project_root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
