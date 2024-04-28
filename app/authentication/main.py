from flask import Blueprint, request, jsonify

from app.database.main import insert_user, verify_user, user_exists
from app.utils.main import is_valid_email

main = Blueprint('main', __name__)


@main.route('/sign-up', methods=['POST'])
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


@main.route('/sign-in', methods=['POST'])
def sign_in():
    data = request.get_json()
    email = data['email']
    password = data['password']

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    authenticated = verify_user(email, password)
    if not authenticated:
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "User successfully signed in"}), 200
