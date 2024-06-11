import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from api.auth import auth_blueprint
from api.cart import cart_blueprint
from api.order import order_blueprint
from api.product import product_blueprint
from api.user import user_blueprint
from api.wishlist import wishlist_blueprint
from database import db
from notification.email_notification import initialize_email_notification_env_variables
from payment.stripe import initialize_stripe
from payment.stripe_product import get_stripe_products
from utils.environment import Environment, get_environment_file
from utils.limiter import limiter

# Determine if running remotely or locally
is_remote = os.getenv('FLASK_REMOTE', 'false').lower() == 'true'

# Load environment variables
if not is_remote:
    env_mode = os.getenv('FLASK_ENV', Environment.Dev.value)
    env_file = get_environment_file(env_mode)
    load_dotenv(env_file)

app = Flask(__name__)

# Enable CORS
if is_remote:
    allowed_client_urls = os.getenv('CORS_ALLOWED_CLIENT_URLS')
    if allowed_client_urls:
        allowed_client_urls_list = allowed_client_urls.split(',')
    else:
        raise ValueError("CORS_ALLOWED_CLIENT_URLS environment variable is not set in production")
    cors = CORS(app, resources={r"/*": {"origins": allowed_client_urls_list}})
else:
    cors = CORS(app)  # Allow all origins in development

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
app.register_blueprint(order_blueprint)
app.register_blueprint(wishlist_blueprint)

# Set database ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('POSTGRES_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()  # Created db tables if not exist

# Initialize Stripe
initialize_stripe()
get_stripe_products()

# Initialize request rate limiter
limiter.init_app(app)

# Notifications
initialize_email_notification_env_variables()

if __name__ == '__main__':
    app.run()
