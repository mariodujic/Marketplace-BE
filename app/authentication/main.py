from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token

from app.database.main import insert_user, verify_user, user_exists
from app.utils.main import is_valid_email

authentication = Blueprint('authentication', __name__)


@authentication.route('/sign-up', methods=['POST'])
def sign_up():
    data = request.get_json()
    email = data['email']
    password = data['password']

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if user_exists(email):
        return jsonify({"error": "User already exists"}), 409

    try:
        insert_user(email, password)
        return jsonify({"message": "User successfully registered"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@authentication.route('/sign-in', methods=['POST'])
def sign_in():
    data = request.get_json()
    email = data['email']
    password = data['password']

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    authenticated = verify_user(email, password)
    if not authenticated:
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)

    return jsonify(
        {"message": "User successfully signed in", "access_token": access_token, "refresh_token": refresh_token}
    ), 200


@authentication.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user, fresh=False)
    return jsonify({'access_token': new_token})
