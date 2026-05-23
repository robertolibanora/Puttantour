import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .db import close_db, init_db, resolve_database_path


def create_app():
    load_dotenv()
    project_root = Path(__file__).resolve().parent.parent
    db_configured = os.getenv('DATABASE_PATH', 'data/game.db')

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    app.config['ADMIN_USERNAME'] = os.getenv('ADMIN_USERNAME', 'admin').strip().lower()
    app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD', 'admin123')
    app.config['DATABASE_PATH'] = str(resolve_database_path(project_root, db_configured))
    app.config['APP_NAME'] = os.getenv('APP_NAME', 'Points Game')

    app.teardown_appcontext(close_db)

    from .routes import register_routes

    @app.context_processor
    def inject_app_globals():
        return {'app_name': app.config['APP_NAME']}

    register_routes(app)

    with app.app_context():
        init_db()

    return app
