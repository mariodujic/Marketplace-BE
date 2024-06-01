from dataclasses import dataclass

from flask import Blueprint, request, jsonify

from database.cart import Cart
from database.cart import CartItem as CartItemDb
from database.user import User
from payment.stripe_product import get_cached_product_by_id
from utils.constants import ResponseKey
from utils.limiter import limiter

cart_blueprint = Blueprint('cart', __name__)


@cart_blueprint.route('/cart', methods=['GET'])
@limiter.limit("100/minute")
def get_user_cart():
    user_id = request.args.get('user_id')
    guest_id = request.args.get('guest_id')

    is_valid, error_message = User.validate_user_id(user_id, guest_id)
    if not is_valid:
        return jsonify({ResponseKey.ERROR.value: error_message}), 400

    cart = Cart.get_cart_by_user_id(user_id=user_id, guest_id=guest_id)

    if cart:
        items = [map_to_cart(item) for item in cart.items]
        return jsonify({ResponseKey.MESSAGE.value: "Cart successfully retrieved", "items": items}), 200
    else:
        return jsonify({ResponseKey.ERROR.value: "Cart not found"}), 404


@cart_blueprint.route('/cart/add', methods=['POST'])
@limiter.limit("100/minute")
def add_item_to_cart():
    data = request.get_json()

    if not data:
        return jsonify({ResponseKey.ERROR.value: "Request data is required"}), 400

    user_id = data.get('user_id')
    guest_id = data.get('guest_id')

    is_valid, error_message = User.validate_user_id(user_id, guest_id)
    if not is_valid:
        return jsonify({ResponseKey.ERROR.value: error_message}), 400

    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({ResponseKey.ERROR.value: "product_id is required"}), 400

    if not isinstance(product_id, str):
        return jsonify({ResponseKey.ERROR.value: "Invalid product_id format, must be a string"}), 400

    product = get_cached_product_by_id(product_id)

    if product.default_price is None or quantity <= 0 or product.default_price.unit_amount < 0:
        return jsonify({ResponseKey.ERROR.value: "Invalid product_id, quantity, or price"}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({ResponseKey.ERROR.value: "Invalid quantity format or value"}), 400

    # Add the item to the cart. If the user is logged in, use user_id. If not, use guest_id.
    # This approach keeps the user and guest carts separate.
    # When a guest user signs in, their guest cart is merged with their user cart and the guest cart is deleted from db.
    Cart.add_item_to_cart(
        product_id=product_id,
        quantity=quantity,
        user_id=user_id if user_id else None,
        guest_id=guest_id if not user_id else None
    )

    return jsonify({ResponseKey.MESSAGE.value: "Item added to cart successfully"}), 201


@cart_blueprint.route('/cart/remove', methods=['POST'])
@limiter.limit("100/minute")
def remove_item_from_cart():
    data = request.get_json()

    if not data:
        return jsonify({ResponseKey.ERROR.value: "Request data is required"}), 400

    user_id = data.get('user_id')
    guest_id = data.get('guest_id')

    is_valid, error_message = User.validate_user_id(user_id, guest_id)
    if not is_valid:
        return jsonify({ResponseKey.ERROR.value: error_message}), 400

    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({ResponseKey.ERROR.value: "product_id is required"}), 400

    if not isinstance(product_id, str):
        return jsonify({ResponseKey.ERROR.value: "Invalid product_id format, must be a string"}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({ResponseKey.ERROR.value: "Invalid quantity format or value"}), 400

    success, message = Cart.remove_item_from_cart(
        product_id=product_id,
        quantity=quantity,
        user_id=user_id,
        guest_id=guest_id
    )
    if success:
        return jsonify({ResponseKey.MESSAGE.value: message}), 200
    else:
        return jsonify({ResponseKey.ERROR.value: message}), 400


@dataclass
class CartItem:
    id: int
    product_id: str
    quantity: int


def map_to_cart(item: CartItemDb) -> CartItem:
    return CartItem(
        id=item.id,
        product_id=item.product_id,
        quantity=item.quantity,
    )
