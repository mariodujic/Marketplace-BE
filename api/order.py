from flask import Blueprint, request, jsonify

from database.cart import Cart
from database.order import Order, OrderStatus
from database.user import User
from payment.stripe_checkout import get_stripe_checkout_session
from payment.stripe_product import get_product_default_price_and_currency, get_cached_product_by_id
from utils.constants import ResponseKey
from utils.limiter import limiter

order_blueprint = Blueprint('order', __name__)


@order_blueprint.route('/order', methods=['GET'])
@limiter.limit("100/minute")
def get_order():
    order_id = request.args.get('order_id')
    user_id = request.args.get('user_id')
    guest_id = request.args.get('guest_id')

    success, order = Order.get_order(order_id, user_id, guest_id)

    if success:
        return jsonify({ResponseKey.MESSAGE.value: "Order successfully retrieved", "order": order}), 200
    else:
        return jsonify({ResponseKey.ERROR.value: order.to_dict()}), 404


@order_blueprint.route('/order/create', methods=['POST'])
@limiter.limit("100/minute")
def create_order():
    data = request.get_json()

    if not data:
        return jsonify({ResponseKey.ERROR.value: "Request data is required"}), 400

    user_id = data.get('user_id')
    guest_id = data.get('guest_id')
    cart_id = data.get('cart_id')

    is_valid, error_message = User.validate_user_id(user_id, guest_id)
    if not is_valid:
        return jsonify({ResponseKey.ERROR.value: error_message}), 400

    if not cart_id:
        return jsonify({ResponseKey.ERROR.value: "Invalid cart_id"}), 400

    # Check if pending order with this cart_id exists and remove it
    success, existing_order = Order.get_order_by_cart_id(cart_id=cart_id, status=OrderStatus.PENDING.value)
    if success:
        Order.cancel_order(existing_order.id)

    # Check if cart exists
    success, result = Cart.get_cart_by_id(cart_id=cart_id)
    if not success:
        return jsonify({ResponseKey.ERROR.value: result}), 404
    cart = result

    items = cart.items
    if not items:
        return jsonify({ResponseKey.ERROR.value: "No items in the cart"}), 400

    success, result = Order.create_order(cart_id=cart_id, user_id=user_id, guest_id=guest_id)

    if not success:
        return jsonify({ResponseKey.ERROR.value: result}), 400

    order = result

    total_amount = 0.0
    currency = None
    for item in items:
        product_id = item.product_id
        quantity = item.quantity

        price, product_currency = get_product_default_price_and_currency(product_id)

        if price is None or quantity <= 0 or price < 0:
            return jsonify({ResponseKey.ERROR.value: "Invalid product_id, quantity, or price"}), 400

        if currency and currency != product_currency:
            return jsonify({ResponseKey.ERROR.value: "Different currencies in order items"}), 400

        currency = product_currency
        total_amount += quantity * price
        Order.add_item_to_order(
            order_id=order.id,
            product_id=product_id,
            quantity=quantity,
            price=price,
            currency=currency
        )

    order.update_total_amount(total_amount=total_amount)

    checkout_created, result = _get_checkout_session(order)

    if not checkout_created:
        return jsonify({ResponseKey.ERROR.value: result}), 400

    checkout_session_url = result.url

    return jsonify(
        {
            ResponseKey.MESSAGE.value: "Order created successfully",
            ResponseKey.ORDER_ID.value: order.id,
            ResponseKey.CHECKOUT_URL.value: checkout_session_url,
        }
    ), 201


def _get_checkout_session(order):
    items = []

    for item in order.items:
        product = get_cached_product_by_id(item.product_id)
        if product:
            price_data = {
                "currency": item.currency,
                "product_data": {
                    "name": product.name,
                    "description": product.description,
                    "images": product.images,
                },
                "unit_amount": int(item.price)
            }
            items.append({
                "price_data": price_data,
                "quantity": item.quantity
            })
        else:
            print(f"Product with ID {item.product_id} not found in cache.")

    user = User.get_by_id(user_id=order.user_id)
    customer_email = user.email if user else None

    return get_stripe_checkout_session(
        order_id=order.id,
        cart_id=order.cart_id,
        customer_email=customer_email,
        items=items
    )


@order_blueprint.route('/order/cancel', methods=['POST'])
@limiter.limit("100/minute")
def cancel_order():
    data = request.get_json()

    if not data:
        return jsonify({ResponseKey.ERROR.value: "Request data is required"}), 400

    order_id = data.get('order_id')

    if not order_id:
        return jsonify({ResponseKey.ERROR.value: "order_id is required"}), 400

    cancel_success, message = Order.cancel_order(order_id=order_id)

    if cancel_success:
        order_success, order = Order.get_order(order_id=order_id)
        if order_success:
            Cart.delete_cart(cart_id=order.cart_id)
        return jsonify({ResponseKey.MESSAGE.value: message}), 200
    else:
        return jsonify({ResponseKey.ERROR.value: message}), 400

# @order_blueprint.route('/webhook/order/update_status', methods=['POST'])
# def update_order_status_stripe_webhook():
# TODO Add Stripe webhooks
