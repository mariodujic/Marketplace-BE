import stripe


# Stripe doc reference: https://docs.stripe.com/api/checkout/sessions/create
def get_stripe_checkout_session(order_id, cart_id, customer_email, items):
    try:
        return True, stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=items,
            mode='payment',
            success_url=f'https://placeholder.com/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url='https://placeholder.com/checkout',
            metadata={
                'order_id': order_id,
                'cart_id': cart_id
            },
            customer_email=customer_email,
            shipping_address_collection={
                'allowed_countries': ['HR']
            }
        )
    except Exception as e:
        return False, str(e)
