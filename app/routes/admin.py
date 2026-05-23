from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..db import get_db, player_totals

bp = Blueprint('admin', __name__)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('user.login'))
        return view(*args, **kwargs)
    return wrapped


@bp.route('/login')
def login_redirect():
    return redirect(url_for('user.login'))


@bp.route('/logout')
def logout():
    return redirect(url_for('user.logout'))


@bp.route('')
@admin_required
def index():
    return redirect(url_for('admin.rules'))


@bp.route('/regole', methods=['GET', 'POST'])
@admin_required
def rules():
    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        try:
            points = int(request.form.get('points', '0'))
        except ValueError:
            points = 0
        if not title:
            flash('Inserisci il testo della regola.', 'error')
        else:
            db.execute('INSERT INTO rules (title, points) VALUES (?, ?)', (title, points))
            db.commit()
            flash('Regola creata.', 'success')
            return redirect(url_for('admin.rules'))
    rules_list = db.execute(
        'SELECT * FROM rules WHERE active = 1 ORDER BY points DESC, title ASC',
    ).fetchall()
    return render_template('admin/rules.html', rules=rules_list)


@bp.route('/regole/<int:rule_id>/elimina', methods=['POST'])
@admin_required
def delete_rule(rule_id):
    db = get_db()
    rule = db.execute('SELECT id FROM rules WHERE id = ? AND active = 1', (rule_id,)).fetchone()
    if not rule:
        flash('Regola non trovata.', 'error')
    else:
        db.execute('UPDATE rules SET active = 0 WHERE id = ?', (rule_id,))
        db.commit()
        flash('Regola eliminata.', 'success')
    return redirect(url_for('admin.rules'))


@bp.route('/classifica')
@admin_required
def classifica():
    return render_template('admin/classifica.html', players=player_totals())


@bp.route('/giocatore/<int:player_id>')
@admin_required
def player_detail(player_id):
    db = get_db()
    player = db.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Giocatore non trovato.', 'error')
        return redirect(url_for('admin.classifica'))
    events = db.execute('''
        SELECT e.*, r.title AS rule_title
        FROM score_events e
        LEFT JOIN rules r ON r.id = e.rule_id
        WHERE e.player_id = ?
        ORDER BY e.created_at DESC, e.id DESC
    ''', (player_id,)).fetchall()
    total = db.execute(
        'SELECT COALESCE(SUM(points), 0) AS total FROM score_events WHERE player_id = ?',
        (player_id,),
    ).fetchone()['total']
    rules_list = db.execute(
        'SELECT * FROM rules WHERE active = 1 ORDER BY points DESC, title ASC',
    ).fetchall()
    return render_template(
        'admin/player_detail.html',
        player=player,
        events=events,
        total=total,
        rules=rules_list,
    )


@bp.route('/giocatore/<int:player_id>/punti', methods=['POST'])
@admin_required
def add_score(player_id):
    db = get_db()
    player = db.execute('SELECT id FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Giocatore non trovato.', 'error')
        return redirect(url_for('admin.classifica'))

    rule_id = request.form.get('rule_id') or None
    note = request.form.get('note', '').strip()
    action = request.form.get('action', 'add')

    if rule_id:
        rule = db.execute('SELECT * FROM rules WHERE id = ? AND active = 1', (rule_id,)).fetchone()
        if not rule:
            flash('Regola non trovata.', 'error')
            return redirect(url_for('admin.player_detail', player_id=player_id))
        points = rule['points']
    else:
        try:
            points = int(request.form.get('custom_points', '0'))
        except ValueError:
            flash('Punti non validi.', 'error')
            return redirect(url_for('admin.player_detail', player_id=player_id))

    if action == 'remove' and points > 0:
        points = -points

    if points == 0:
        flash('Indica un valore diverso da zero.', 'error')
        return redirect(url_for('admin.player_detail', player_id=player_id))

    db.execute(
        'INSERT INTO score_events (player_id, rule_id, points, note, judge_username) VALUES (?, ?, ?, ?, ?)',
        (player_id, rule_id, points, note or None, session.get('admin_username')),
    )
    db.commit()
    flash('Punteggio aggiornato.', 'success')
    return redirect(url_for('admin.player_detail', player_id=player_id))


@bp.route('/giocatore/<int:player_id>/eventi/<int:event_id>/elimina', methods=['POST'])
@admin_required
def delete_event(player_id, event_id):
    db = get_db()
    event = db.execute(
        'SELECT id FROM score_events WHERE id = ? AND player_id = ?',
        (event_id, player_id),
    ).fetchone()
    if not event:
        flash('Evento non trovato.', 'error')
    else:
        db.execute('DELETE FROM score_events WHERE id = ?', (event_id,))
        db.commit()
        flash('Evento rimosso dallo storico.', 'success')
    return redirect(url_for('admin.player_detail', player_id=player_id))


@bp.route('/giocatore/<int:player_id>/squalifica', methods=['POST'])
@admin_required
def disqualify(player_id):
    db = get_db()
    player = db.execute('SELECT id FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Giocatore non trovato.', 'error')
        return redirect(url_for('admin.classifica'))
    db.execute('UPDATE players SET disqualified = 1 WHERE id = ?', (player_id,))
    db.commit()
    flash('Giocatore squalificato.', 'success')
    return redirect(url_for('admin.player_detail', player_id=player_id))


@bp.route('/giocatore/<int:player_id>/riabilita', methods=['POST'])
@admin_required
def requalify(player_id):
    db = get_db()
    player = db.execute('SELECT id FROM players WHERE id = ?', (player_id,)).fetchone()
    if not player:
        flash('Giocatore non trovato.', 'error')
        return redirect(url_for('admin.classifica'))
    db.execute('UPDATE players SET disqualified = 0 WHERE id = ?', (player_id,))
    db.commit()
    flash('Giocatore riabilitato in classifica.', 'success')
    return redirect(url_for('admin.player_detail', player_id=player_id))
