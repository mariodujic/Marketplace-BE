import os

from flask import Blueprint, request, jsonify

from database.cart import Cart
from database.order import Order, OrderStatus
from database.user import User
from payment.stripe_checkout import get_stripe_checkout_session, get_checkout_session_info, get_checkout_event
from payment.stripe_product import get_cached_product_by_id
from utils.common import safe_int
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
    cart = Cart.get_cart_by_user_id(user_id, guest_id)
    if not cart:
        return jsonify({ResponseKey.ERROR.value: "Cart does not exist"}), 404

    if not cart.items or len(cart.items) == 0:
        return jsonify({ResponseKey.ERROR.value: "No items in the cart"}), 400

    is_valid, error_message = User.validate_user_id(user_id, guest_id)
    if not is_valid:
        return jsonify({ResponseKey.ERROR.value: error_message}), 400

    success, existing_order = Order.get_order_by_cart_id_for_status(cart_id=cart.id, status=OrderStatus.PENDING.value)
    if success:
        Order.cancel_order(existing_order.id)

    # Check if cart exists
    success, result = Cart.get_cart_by_id(cart_id=cart.id)
    if not success:
        return jsonify({ResponseKey.ERROR.value: result}), 404
    cart = result

    items = cart.items
    if not items:
        return jsonify({ResponseKey.ERROR.value: "No items in the cart"}), 400

    success, result = Order.create_order(cart_id=cart.id, user_id=user_id, guest_id=guest_id)

    if not success:
        return jsonify({ResponseKey.ERROR.value: result}), 400

    order = result

    total_amount = 0.0
    currency = None
    for item in items:
        product_id = item.product_id
        quantity = item.quantity

        product = get_cached_product_by_id(product_id)

        if product.default_price is None or quantity <= 0 or product.default_price.unit_amount < 0:
            return jsonify({ResponseKey.ERROR.value: "Invalid product_id, quantity, or price"}), 400

        if currency and currency != product.default_price.currency:
            return jsonify({ResponseKey.ERROR.value: "Different currencies in order items"}), 400

        currency = product.default_price.currency
        total_amount += quantity * product.default_price.unit_amount

        discount = product.metadata.get('discount')
        price = product.default_price.unit_amount
        # Lower the price for discount if exists
        if discount and 0 < safe_int(discount) < 100:
            price = product.default_price.unit_amount * (1 - safe_int(discount) / 100)

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


@order_blueprint.route('/order/checkout/success', methods=['POST'])
@limiter.limit("100/minute")
def update_order_status_on_checkout_success():
    data = request.get_json()

    if not data:
        return jsonify({ResponseKey.ERROR.value: "Request data is required"}), 400

    session_id = data.get('session_id')
    if not session_id:
        return jsonify({ResponseKey.ERROR.value: "session_id is required"}), 400

    session = get_checkout_session_info(session_id)
    if session.payment_status != 'paid':
        return jsonify({ResponseKey.ERROR.value: "Payment not completed"}), 400

    order_id = session.metadata.get('order_id')
    if not order_id:
        return jsonify({ResponseKey.ERROR.value: "Order ID not found in session metadata"}), 400

    success, order = Order.get_order(order_id=order_id)
    if not success:
        return jsonify({ResponseKey.ERROR.value: "Order not found"}), 404

    if order.status == OrderStatus.PAID.value:
        return jsonify({ResponseKey.MESSAGE.value: "Order already marked as PAID", "order_id": order_id}), 200

    order.update_order_status(order_id, OrderStatus.PAID.value)

    cart_id = session.metadata.get('cart_id')
    if cart_id:
        Cart.delete_cart(cart_id=cart_id)

    return jsonify({ResponseKey.MESSAGE.value: "Order completed successfully", "order_id": order_id}), 200


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


@order_blueprint.route('/webhook/order/paid', methods=['POST'])
def paid_order_status_stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    valid_event, event = get_checkout_event(payload, sig_header, endpoint_secret)

    if not valid_event:
        return jsonify({"error": event}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        if session['payment_status'] == 'paid':
            order_id = session['metadata'].get('order_id')
            if not order_id:
                return jsonify({"error": "Order ID not found in session metadata"}), 400

            success, order = Order.get_order(order_id=order_id)
            if not success:
                return jsonify({"error": "Order not found"}), 404

            if order.status == OrderStatus.PAID.value:
                return jsonify({ResponseKey.MESSAGE.value: "Order already marked as PAID"}), 200

            order.update_order_status(order_id, OrderStatus.PAID.value)

            cart_id = session['metadata'].get('cart_id')
            if cart_id:
                Cart.delete_cart(cart_id=cart_id)

            return jsonify({"message": "Order status updated to PAID"}), 200

    return jsonify({"message": "Event received"}), 200
