from flask import Flask

from .admin import bp as admin_bp
from .user import bp as user_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
