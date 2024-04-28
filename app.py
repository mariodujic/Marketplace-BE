import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager

from app.authentication.main import authentication
from app.database.main import create_users_table

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load JWT config
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(authentication)

# Create missing tables
create_users_table()

if __name__ == '__main__':
    app.run(debug=os.getenv('DEBUG', 'False') == 'True')
