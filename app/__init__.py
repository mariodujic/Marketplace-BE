from flask import Flask
from app.authentication.main import main


def create_app():
    app = Flask(__name__)
    app.register_blueprint(main)
    return app
