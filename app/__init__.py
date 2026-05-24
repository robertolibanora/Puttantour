import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .db import close_db, init_db, resolve_database_path
from .judges import load_admin_judges
from .timezone import format_rome_datetime


def create_app():
    load_dotenv()
    project_root = Path(__file__).resolve().parent.parent
    db_configured = os.getenv('DATABASE_PATH', 'data/game.db')

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    app.config['ADMIN_JUDGES'] = load_admin_judges()
    app.config['DATABASE_PATH'] = str(resolve_database_path(project_root, db_configured))
    app.config['APP_NAME'] = os.getenv('APP_NAME', 'PUTTANTOUR')
    app.config['TIMEZONE'] = 'Europe/Rome'

    app.jinja_env.filters['rome_time'] = format_rome_datetime

    app.teardown_appcontext(close_db)

    from .routes import register_routes

    @app.context_processor
    def inject_app_globals():
        return {'app_name': app.config['APP_NAME']}

    register_routes(app)

    with app.app_context():
        init_db()

    return app
