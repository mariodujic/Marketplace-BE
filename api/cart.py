from flask import Blueprint, request, jsonify

from database.cart import Cart

cart_blueprint = Blueprint('cart', __name__)


@cart_blueprint.route('/cart', methods=['GET'])
def get_user_cart_by_user_id():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user_id format"}), 400

    cart = Cart.get_cart_by_user_id(user_id)

    if cart:
        return jsonify({"message": "Cart successfully retrieved", "cart": cart}), 200
    else:
        return jsonify({"error": "Cart not found"}), 404


@cart_blueprint.route('/cart/add', methods=['POST'])
def add_item_to_cart():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request data is required"}), 400

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({"error": "user_id and product_id are required"}), 400

    if not isinstance(product_id, str):
        return jsonify({"error": "Invalid product_id format, must be a string"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user_id format"}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Invalid quantity format or value"}), 400

    Cart.add_item_to_cart(user_id, product_id, quantity)

    return jsonify({"message": "Item added to cart successfully"}), 201


@cart_blueprint.route('/cart/remove', methods=['POST'])
def remove_item_from_cart():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request data is required"}), 400

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({"error": "user_id and product_id are required"}), 400

    if not isinstance(product_id, str):
        return jsonify({"error": "Invalid product_id format, must be a string"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user_id format"}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Invalid quantity format or value"}), 400

    try:
        Cart.remove_item_from_cart(user_id, product_id, quantity)
        return jsonify({"message": "Item removed from cart successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
