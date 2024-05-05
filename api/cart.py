from flask import Blueprint, request, jsonify

from database.cart import Cart
from database.user import User
from utils.limiter import limiter

cart_blueprint = Blueprint('cart', __name__)


@cart_blueprint.route('/cart', methods=['GET'])
@limiter.limit("100/minute")
def get_user_cart():
    user_id = request.args.get('user_id')
    guest_id = request.args.get('guest_id')

    is_valid, error_message = validate_user_id(user_id, guest_id)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    cart = Cart.get_cart(user_id=user_id, guest_id=guest_id)

    if cart:
        return jsonify({"message": "Cart successfully retrieved", "cart": cart.to_dict()}), 200
    else:
        return jsonify({"error": "Cart not found"}), 404


@cart_blueprint.route('/cart/add', methods=['POST'])
@limiter.limit("100/minute")
def add_item_to_cart():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request data is required"}), 400

    user_id = data.get('user_id')
    guest_id = data.get('guest_id')

    is_valid, error_message = validate_user_id(user_id, guest_id)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    if not isinstance(product_id, str):
        return jsonify({"error": "Invalid product_id format, must be a string"}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Invalid quantity format or value"}), 400

    Cart.add_item_to_cart(product_id=product_id, quantity=quantity, user_id=user_id, guest_id=guest_id)

    response = jsonify({"message": "Item added to cart successfully"})

    return response, 201


@cart_blueprint.route('/cart/remove', methods=['POST'])
@limiter.limit("100/minute")
def remove_item_from_cart():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request data is required"}), 400

    user_id = data.get('user_id')
    guest_id = data.get('guest_id')

    is_valid, error_message = validate_user_id(user_id, guest_id)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    if not isinstance(product_id, str):
        return jsonify({"error": "Invalid product_id format, must be a string"}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Invalid quantity format or value"}), 400

    try:
        Cart.remove_item_from_cart(product_id=product_id, quantity=quantity, user_id=user_id, guest_id=guest_id)
        return jsonify({"message": "Item removed from cart successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


def validate_user_id(user_id, guest_id):
    if not user_id and not guest_id:
        return False, "Either user_id or guest_id is required"

    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            return False, "Invalid user_id format"

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return False, "User does not exist"

    if guest_id and (not isinstance(guest_id, str) or guest_id.strip() == ""):
        return False, "Invalid guest_id format"

    return True, None
