import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager

from api.auth import auth_blueprint
from api.cart import cart_blueprint
from api.product import product_blueprint
from api.user import user_blueprint
from database import db
from payment.stripe import initialize_stripe
from utils.limiter import limiter

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load JWT config
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
jwt = JWTManager(app)

# Register api
app.register_blueprint(auth_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(product_blueprint)
app.register_blueprint(cart_blueprint)

# Set database ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('POSTGRES_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()  # Created db tables if not exist

initialize_stripe()

# Initialize request rate limiter
limiter.init_app(app)

if __name__ == '__main__':
    app.run(debug=os.getenv('DEBUG', 'False') == 'True')
