import json

from flask import Blueprint, Response, current_app, render_template, send_from_directory

bp = Blueprint('pwa', __name__)

THEME_COLOR = '#f4acb7'
BACKGROUND_COLOR = '#f1ebe6'


@bp.route('/manifest.webmanifest')
def manifest():
    app_name = current_app.config['APP_NAME']
    short_name = app_name if len(app_name) <= 12 else app_name[:12].rstrip()
    payload = {
        'id': '/',
        'name': app_name,
        'short_name': short_name,
        'description': 'Classifica live, profilo giocatore e gestione punti.',
        'lang': 'it',
        'dir': 'ltr',
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'display_override': ['standalone', 'minimal-ui', 'browser'],
        'orientation': 'portrait-primary',
        'background_color': BACKGROUND_COLOR,
        'theme_color': THEME_COLOR,
        'categories': ['games', 'social'],
        'icons': [
            {
                'src': '/static/icons/icon-192.png',
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any',
            },
            {
                'src': '/static/icons/icon-512.png',
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'any',
            },
            {
                'src': '/static/icons/maskable-512.png',
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'maskable',
            },
        ],
        'shortcuts': [
            {
                'name': 'Classifica',
                'short_name': 'Classifica',
                'description': 'Apri la classifica live',
                'url': '/classifica',
                'icons': [{'src': '/static/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'}],
            },
            {
                'name': 'Accedi',
                'short_name': 'Accedi',
                'description': 'Accedi al gioco',
                'url': '/login',
                'icons': [{'src': '/static/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'}],
            },
        ],
    }
    response = Response(json.dumps(payload, ensure_ascii=False), mimetype='application/manifest+json')
    response.headers['Cache-Control'] = 'no-cache'
    return response


@bp.route('/sw.js')
def service_worker():
    response = send_from_directory(current_app.static_folder, 'js/sw.js')
    response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Service-Worker-Allowed'] = '/'
    return response


@bp.route('/offline')
def offline():
    return render_template('shared/offline.html')
