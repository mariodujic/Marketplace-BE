from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.user import User
from utils.constants import ResponseKey
from utils.limiter import limiter

user_blueprint = Blueprint('user', __name__)


@user_blueprint.route('/user', methods=['GET'])
@limiter.limit("200/minute")
@jwt_required()
def get_user_profile():
    current_user_email = get_jwt_identity()
    current_user = User.get_by_email(current_user_email)
    if current_user:
        return jsonify(current_user.to_dict()), 200
    else:
        return jsonify({ResponseKey.ERROR.value: "User not found"}), 404


@user_blueprint.route('/user', methods=['PATCH'])
@limiter.limit("200/minute")
@jwt_required()
def update_user_profile():
    current_user_email = get_jwt_identity()
    current_user = User.get_by_email(current_user_email)

    if not current_user:
        return jsonify({ResponseKey.ERROR.value: "User not found"}), 404

    if not current_user.active:
        return jsonify({ResponseKey.ERROR.value: "User profile cannot be updated because the account is inactive"}), 403

    data = request.get_json()

    if 'active' in data:
        return jsonify(
            {ResponseKey.ERROR.value: "Changes to activation status must be handled via the dedicated endpoints"}
        ), 403

    success = current_user.update(data)
    if success:
        return jsonify({ResponseKey.MESSAGE.value: "User updated successfully", "user": current_user.to_dict()}), 200
    else:
        return jsonify({ResponseKey.ERROR.value: "Failed to update user"}), 500


@user_blueprint.route('/user/deactivate', methods=['POST'])
@limiter.limit("60/minute")
@jwt_required()
def deactivate_user():
    current_user_email = get_jwt_identity()
    current_user = User.get_by_email(current_user_email)
    if not current_user:
        return jsonify({ResponseKey.ERROR.value: "User not found"}), 404

    if not current_user.active:
        return jsonify({ResponseKey.MESSAGE.value: "User is already deactivated"}), 409

    success = current_user.update({'active': False})
    if success:
        return jsonify({ResponseKey.MESSAGE.value: "User deactivated successfully"}), 200
    else:
        return jsonify({ResponseKey.ERROR.value: "Failed to deactivate user"}), 500
