import os

import stripe


# Stripe doc reference: https://docs.stripe.com/api/checkout/sessions/create
def get_stripe_checkout_session(order_id, cart_id, customer_email, items):
    try:
        post_checkout_url = os.getenv('STRIPE_POST_CHECKOUT_SESSION_URL', '')
        return True, stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=items,
            mode='payment',
            success_url=f'{post_checkout_url}/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{post_checkout_url}/cart',
            metadata={
                'order_id': order_id,
                'cart_id': cart_id
            },
            customer_email=customer_email,
            shipping_address_collection={
                'allowed_countries': ['HR', 'BA']
            }
        )
    except Exception as e:
        return False, str(e)
