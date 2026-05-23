import re
import sqlite3
from functools import wraps

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db, player_totals

bp = Blueprint('user', __name__)


def player_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('player_id'):
            flash('Accedi per continuare.', 'error')
            return redirect(url_for('user.login'))
        return view(*args, **kwargs)
    return wrapped


@bp.context_processor
def inject_user_globals():
    player = None
    pid = session.get('player_id')
    if pid:
        player = get_db().execute('SELECT id, name FROM players WHERE id = ?', (pid,)).fetchone()
    return {'current_player': player}


@bp.route('/')
def index():
    if session.get('player_id'):
        return redirect(url_for('user.classifica'))
    return redirect(url_for('user.login'))


@bp.route('/classifica')
@player_required
def classifica():
    pid = session['player_id']
    rank_position = None
    for i, p in enumerate(player_totals(), start=1):
        if p['id'] == pid and not p['disqualified']:
            rank_position = i
            break
    return render_template(
        'user/classifica.html',
        players=player_totals(),
        my_rank=rank_position,
    )


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('player_id'):
        return redirect(url_for('user.classifica'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        if not name or not username or not password:
            flash('Compila tutti i campi obbligatori.', 'error')
        elif len(password) < 6:
            flash('La password deve essere di almeno 6 caratteri.', 'error')
        elif password != password2:
            flash('Le password non coincidono.', 'error')
        elif not re.fullmatch(r'[a-zA-Z0-9._-]{3,32}', username):
            flash('Il nome utente deve essere 3–32 caratteri (lettere, numeri, . _ -).', 'error')
        elif username == current_app.config['ADMIN_USERNAME']:
            flash('Questo nome utente non è disponibile.', 'error')
        else:
            db = get_db()
            taken = db.execute(
                'SELECT 1 FROM players WHERE username = ?',
                (username,),
            ).fetchone()
            if taken:
                flash('Questo nome utente è già in uso.', 'error')
            elif db.execute('SELECT 1 FROM players WHERE name = ?', (name,)).fetchone():
                flash('Questo nome in classifica è già usato. Scegline un altro.', 'error')
            else:
                try:
                    db.execute(
                        'INSERT INTO players (name, username, password_hash) VALUES (?, ?, ?)',
                        (name, username, generate_password_hash(password)),
                    )
                    db.commit()
                    row = db.execute('SELECT id FROM players WHERE username = ?', (username,)).fetchone()
                    session['player_id'] = row['id']
                    flash('Registrazione completata. Benvenuto in classifica.', 'success')
                    return redirect(url_for('user.classifica'))
                except sqlite3.IntegrityError:
                    db.rollback()
                    flash('Nome utente o nome in classifica già esistente.', 'error')
    return render_template('user/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('is_admin'):
        return redirect(url_for('admin.rules'))
    if session.get('player_id'):
        return redirect(url_for('user.classifica'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Inserisci nome utente e password.', 'error')
        elif username == current_app.config['ADMIN_USERNAME']:
            if password == current_app.config['ADMIN_PASSWORD']:
                session.pop('player_id', None)
                session['is_admin'] = True
                session.permanent = True
                flash('Accesso giudice effettuato.', 'success')
                return redirect(url_for('admin.rules'))
            flash('Credenziali non valide.', 'error')
        else:
            db = get_db()
            row = db.execute(
                'SELECT id, password_hash FROM players WHERE username = ?',
                (username,),
            ).fetchone()
            if not row or not row['password_hash'] or not check_password_hash(row['password_hash'], password):
                flash('Credenziali non valide.', 'error')
            else:
                session.pop('is_admin', None)
                session.permanent = True
                session['player_id'] = row['id']
                flash('Accesso effettuato.', 'success')
                return redirect(url_for('user.classifica'))
    return render_template('shared/login.html')


@bp.route('/logout')
def logout():
    session.pop('is_admin', None)
    session.pop('player_id', None)
    flash('Logout effettuato.', 'success')
    return redirect(url_for('user.login'))


@bp.route('/profilo')
@player_required
def profilo():
    player_id = session['player_id']
    db = get_db()
    player = db.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    events = db.execute('''
        SELECT e.*, r.title AS rule_title
        FROM score_events e
        LEFT JOIN rules r ON r.id = e.rule_id
        WHERE e.player_id = ?
        ORDER BY e.created_at DESC, e.id DESC
        LIMIT 20
    ''', (player_id,)).fetchall()
    total = db.execute(
        'SELECT COALESCE(SUM(points), 0) AS total FROM score_events WHERE player_id = ?',
        (player_id,),
    ).fetchone()['total']
    my_rank = None
    if not player['disqualified']:
        for i, p in enumerate(player_totals(), start=1):
            if p['id'] == player_id and not p['disqualified']:
                my_rank = i
                break
    return render_template(
        'user/profilo.html',
        player=player,
        events=events,
        total=total,
        my_rank=my_rank,
    )
