import os
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token

from database.cart import Cart
from database.user import User
from notification.email_notification import send_password_reset_email
from utils.common import is_valid_email
from utils.constants import ResponseKey
from utils.limiter import limiter

auth_blueprint = Blueprint('auth', __name__)

# Reset password tokens are stored in memory to avoid additional database table. Tokens are cleared once expired.
RESET_PASSWORD_TOKEN_EXPIRY = timedelta(hours=1)
reset_tokens = {}


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


@auth_blueprint.route('/reset-password', methods=['POST'])
@limiter.limit("10/minute")
def reset_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({ResponseKey.ERROR.value: "Email is required"}), 400

    if not is_valid_email(email):
        return jsonify({ResponseKey.ERROR.value: "Invalid email format"}), 400

    user = User.get_by_email(email)
    if not user:
        return jsonify({ResponseKey.ERROR.value: "User does not exist"}), 404

    reset_token = str(uuid.uuid4())
    reset_token_expiry = datetime.utcnow() + RESET_PASSWORD_TOKEN_EXPIRY

    reset_tokens[reset_token] = {
        "email": email,
        "expiry": reset_token_expiry
    }

    client_url = os.getenv("CLIENT_URL")
    reset_link = f"{client_url}/reset-password?token={reset_token}"
    send_password_reset_email(email, reset_link)

    return jsonify({ResponseKey.MESSAGE.value: "Password reset link has been sent to your email"}), 200


@auth_blueprint.route('/update-password/<reset_token>', methods=['POST'])
@limiter.limit("10/minute")
def update_password(reset_token):
    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({ResponseKey.ERROR.value: "New password is required"}), 400

    token_data = reset_tokens.get(reset_token)

    if not token_data or token_data['expiry'] < datetime.utcnow():
        return jsonify({ResponseKey.ERROR.value: "Invalid or expired reset token"}), 400

    email = token_data['email']
    user = User.get_by_email(email)

    if not user:
        return jsonify({ResponseKey.ERROR.value: "User does not exist"}), 404

    updates = {'password': new_password}
    if not user.update(updates):
        return jsonify({ResponseKey.ERROR.value: "Failed to update password"}), 500

    del reset_tokens[reset_token]
    _clear_expired_reset_password_tokens()

    return jsonify({ResponseKey.MESSAGE.value: "Password has been updated successfully"}), 200


def _clear_expired_reset_password_tokens():
    current_time = datetime.utcnow()
    expired_tokens = [token for token, data in reset_tokens.items() if data['expiry'] < current_time]
    for token in expired_tokens:
        del reset_tokens[token]
