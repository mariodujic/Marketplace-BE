from dataclasses import dataclass

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.user import User
from database.wishlist import Wishlist
from database.wishlist import WishlistItem as WishlistItemDB
from utils.constants import ResponseKey
from utils.limiter import limiter

wishlist_blueprint = Blueprint('wishlist', __name__)


@wishlist_blueprint.route('/wishlist', methods=['GET'])
@limiter.limit("100/minute")
@jwt_required()
def get_user_wishlist():
    user_email = get_jwt_identity()
    user = User.get_by_email(user_email)

    if not user:
        return jsonify({ResponseKey.ERROR.value: "User not found"}), 404

    wishlist = Wishlist.get_wishlist(user_id=user.id)

    if wishlist:
        return jsonify(
            {
                ResponseKey.MESSAGE.value: "Wishlist successfully retrieved",
                "wishlist": [map_wishlist_item(item) for item in wishlist.items]
            }
        ), 200
    else:
        return jsonify({ResponseKey.ERROR.value: "Wishlist not found"}), 404


@wishlist_blueprint.route('/wishlist/add', methods=['POST'])
@limiter.limit("100/minute")
@jwt_required()
def add_item_to_wishlist():
    user_email = get_jwt_identity()
    user = User.get_by_email(user_email)

    if not user:
        return jsonify({ResponseKey.ERROR.value: "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({ResponseKey.ERROR.value: "Request data is required"}), 400

    user_id = user.id
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({ResponseKey.ERROR.value: "product_id is required"}), 400

    Wishlist.add_item_to_wishlist(product_id=product_id, user_id=user_id)
    return jsonify({ResponseKey.MESSAGE.value: "Item added to wishlist successfully"}), 201


@wishlist_blueprint.route('/wishlist/remove', methods=['POST'])
@limiter.limit("100/minute")
@jwt_required()
def remove_item_from_wishlist():
    user_email = get_jwt_identity()
    user = User.get_by_email(user_email)

    if not user:
        return jsonify({ResponseKey.ERROR.value: "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({ResponseKey.ERROR.value: "Request data is required"}), 400

    user_id = user.id
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({ResponseKey.ERROR.value: "product_id is required"}), 400

    success, message = Wishlist.remove_item_from_wishlist(product_id=product_id, user_id=user_id)
    if success:
        return jsonify({ResponseKey.MESSAGE.value: message}), 200
    else:
        return jsonify({ResponseKey.ERROR.value: message}), 400


@dataclass
class WishlistItem:
    id: int
    product_id: str


def map_wishlist_item(item: WishlistItemDB) -> WishlistItem:
    return WishlistItem(
        id=item.id,
        product_id=item.product_id
    )
