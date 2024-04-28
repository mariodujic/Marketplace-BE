from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.user import User

user = Blueprint('user', __name__)


@user.route('/user', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user_email = get_jwt_identity()
    current_user = User.get_by_email(current_user_email)
    if current_user:
        return jsonify(current_user.to_dict()), 200
    else:
        return jsonify({"error": "User not found"}), 404


@user.route('/user', methods=['PATCH'])
@jwt_required()
def update_user_profile():
    current_user_email = get_jwt_identity()
    current_user = User.get_by_email(current_user_email)

    if not current_user:
        return jsonify({"error": "User not found"}), 404

    if not current_user.active:
        return jsonify({"error": "User profile cannot be updated because the account is inactive"}), 403

    data = request.get_json()

    if 'active' in data:
        return jsonify({"error": "Changes to activation status must be handled via the dedicated endpoints"}), 403

    success = current_user.update(data)
    if success:
        return jsonify({"message": "User updated successfully", "user": current_user.to_dict()}), 200
    else:
        return jsonify({"error": "Failed to update user"}), 500


@user.route('/user/deactivate', methods=['POST'])
@jwt_required()
def deactivate_user():
    current_user_email = get_jwt_identity()
    current_user = User.get_by_email(current_user_email)
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    if not current_user.active:
        return jsonify({"message": "User is already deactivated"}), 409

    success = current_user.update({'active': False})
    if success:
        return jsonify({"message": "User deactivated successfully"}), 200
    else:
        return jsonify({"error": "Failed to deactivate user"}), 500
