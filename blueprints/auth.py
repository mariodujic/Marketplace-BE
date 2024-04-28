from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token

from database.user import User
from utils.main import is_valid_email

auth = Blueprint('auth', __name__)


@auth.route('/sign-up', methods=['POST'])
def sign_up():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if User.user_exists(email):
        return jsonify({"error": "User already exists"}), 409

    new_user = User.create_user(email, password)
    if new_user:
        return jsonify({"message": "User successfully registered"}), 201
    else:
        return jsonify({"error": "Failed to register user"}), 500


@auth.route('/sign-in', methods=['POST'])
def sign_in():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if User.verify_user(email, password):
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify({"message": "User successfully signed in", "access_token": access_token,
                        "refresh_token": refresh_token}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


@auth.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user, fresh=False)
    return jsonify({'access_token': new_token})
