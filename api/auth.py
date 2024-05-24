from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token

from database.cart import Cart
from database.user import User
from utils.constants import ResponseKey
from utils.limiter import limiter
from utils.common import is_valid_email

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/sign-up', methods=['POST'])
@limiter.limit("100/minute")
def sign_up():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({ResponseKey.ERROR.value: "Email and password are required"}), 400

    if not is_valid_email(email):
        return jsonify({ResponseKey.ERROR.value: "Invalid email format"}), 400

    if User.user_exists(email):
        return jsonify({ResponseKey.ERROR.value: "User already exists"}), 409

    new_user = User.create_user(email, password)
    if new_user:
        return jsonify({ResponseKey.MESSAGE.value: "User successfully registered"}), 201
    else:
        return jsonify({ResponseKey.ERROR.value: "Failed to register user"}), 500


@auth_blueprint.route('/sign-in', methods=['POST'])
@limiter.limit("100/minute")
def sign_in():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({ResponseKey.ERROR.value: "Email and password are required"}), 400

    user = User.get_by_email(email=email)
    if user is None:
        return jsonify({ResponseKey.ERROR.value: "Email does not exist"}), 401

    if User.verify_user(email, password):
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        response = {
            ResponseKey.MESSAGE.value: "User successfully signed in",
            ResponseKey.ACCESS_TOKEN.value: access_token,
            ResponseKey.REFRESH_TOKEN.value: refresh_token,
            ResponseKey.USER.value: user.to_dict()
        }

        user_id = user.id
        guest_id = data.get('guest_id')
        if guest_id:
            # TODO Should I create dedicated cart API to check if merge is required?
            merge_result = Cart.merge_carts(guest_id, user_id)
            if merge_result != "Cart merged successfully":
                response[ResponseKey.CART_ERROR.value] = merge_result
            else:
                response[ResponseKey.CART_MESSAGE.value] = merge_result

        return jsonify(response), 200
    else:
        return jsonify({ResponseKey.ERROR.value: "Invalid email or password"}), 401


@auth_blueprint.route('/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user, fresh=False)
    return jsonify({ResponseKey.ACCESS_TOKEN.value: new_token}), 200
