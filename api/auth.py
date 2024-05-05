from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token

from database.cart import Cart
from database.user import User
from utils.limiter import limiter
from utils.main import is_valid_email

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/sign-up', methods=['POST'])
@limiter.limit("100/minute")
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


@auth_blueprint.route('/sign-in', methods=['POST'])
@limiter.limit("100/minute")
def sign_in():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({"error": "Email does not exist"}), 401

    if User.verify_user(email, password):
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        response = {
            "message": "User successfully signed in",
            "access_token": access_token,
            "refresh_token": refresh_token
        }

        user_id = user.id
        guest_id = data.get('guest_id')
        if guest_id:
            merge_result = Cart.merge_carts(guest_id, user_id)
            if merge_result != "Cart merged successfully":
                response["cart_error"] = merge_result
            else:
                response["cart_message"] = merge_result

        return jsonify(response), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


@auth_blueprint.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user, fresh=False)
    return jsonify({'access_token': new_token})
