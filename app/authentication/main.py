from flask import Blueprint, request, jsonify
from app.database.main import insert_user
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

    try:
        insert_user(email, password)
        return jsonify({"message": "User successfully registered"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
