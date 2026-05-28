from functools import wraps

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from ..avatars import AVATAR_BG_COLORS, AVATAR_BG_SLUGS, AVATAR_EMOJIS
from ..db import active_rules, get_db, player_totals, recent_score_events

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
        player = get_db().execute(
            'SELECT id, name, avatar_emoji, avatar_bg FROM players WHERE id = ?',
            (pid,),
        ).fetchone()
    return {'current_player': player}


@bp.route('/')
def index():
    if session.get('player_id'):
        return redirect(url_for('user.classifica'))
    return redirect(url_for('user.login'))


@bp.route('/news')
@player_required
def news():
    return render_template('user/news.html', events=recent_score_events(limit=5))


@bp.route('/regole')
@player_required
def regole():
    return render_template('user/regole.html', rules=active_rules())


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


@bp.route('/pubblica')
def classifica_pubblica():
    return render_template(
        'shared/classifica_public.html',
        players=player_totals(),
    )


@bp.route('/register')
def register():
    flash('Le iscrizioni sono chiuse.', 'error')
    return redirect(url_for('user.login'))


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
        elif username in current_app.config['ADMIN_JUDGES']:
            if password == current_app.config['ADMIN_JUDGES'][username]:
                session.pop('player_id', None)
                session['is_admin'] = True
                session['admin_username'] = username
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
    session.pop('admin_username', None)
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
        avatar_emojis=AVATAR_EMOJIS,
        avatar_bg_colors=AVATAR_BG_COLORS,
    )


@bp.route('/profilo/avatar', methods=['POST'])
@player_required
def profilo_avatar():
    db = get_db()
    player = db.execute(
        'SELECT avatar_emoji, avatar_bg FROM players WHERE id = ?',
        (session['player_id'],),
    ).fetchone()
    if player['avatar_emoji'] and player['avatar_bg']:
        flash('L’avatar non può essere modificato.', 'error')
        return redirect(url_for('user.profilo'))

    emoji = request.form.get('avatar_emoji', '').strip()
    bg = request.form.get('avatar_bg', '').strip()
    if emoji not in AVATAR_EMOJIS:
        flash('Emoji non valida.', 'error')
    elif bg not in AVATAR_BG_SLUGS:
        flash('Colore non valido.', 'error')
    else:
        updated = db.execute(
            '''
            UPDATE players
            SET avatar_emoji = ?, avatar_bg = ?
            WHERE id = ? AND avatar_emoji IS NULL AND avatar_bg IS NULL
            ''',
            (emoji, bg, session['player_id']),
        )
        db.commit()
        if updated.rowcount:
            flash('Avatar scelto. La scelta è definitiva.', 'success')
        else:
            flash('L’avatar non può essere modificato.', 'error')
    return redirect(url_for('user.profilo'))
