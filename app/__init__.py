from flask import Flask
from .extensions import db, migrate, login_manager, bcrypt
from .routes import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(main_bp)

    # Crează toate tabelele
    with app.app_context():
        db.create_all()

    return app
