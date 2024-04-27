from flask import Blueprint, request, jsonify
from app.database.user import insert_user

main = Blueprint('main', __name__)


@main.route('/sign-up', methods=['POST'])
def sign_up():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone_number = request.form['phone_number']
    address = request.form['address']
    password = request.form['password']

    try:
        insert_user(first_name, last_name, email, phone_number, address, password)
        return jsonify({"message": "User successfully registered"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
