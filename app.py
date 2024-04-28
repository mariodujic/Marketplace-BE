import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager

from blueprints.auth import auth
from database import db

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load JWT config
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth)
# Set database ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('POSTGRES_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()  # Created db tables if not exist

if __name__ == '__main__':
    app.run(debug=os.getenv('DEBUG', 'False') == 'True')
