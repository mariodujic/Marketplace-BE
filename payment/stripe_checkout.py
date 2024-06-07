import os
from dataclasses import dataclass, field
from typing import Dict

import stripe


# Stripe doc reference: https://docs.stripe.com/api/checkout/sessions/create
def get_stripe_checkout_session(order_id, cart_id, customer_email, items):
    try:
        post_checkout_url = os.getenv('STRIPE_POST_CHECKOUT_SESSION_URL', '')
        return True, stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=items,
            mode='payment',
            success_url=f'{post_checkout_url}/checkout-success?session_id={{CHECKOUT_SESSION_ID}}',
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


@dataclass
class SessionDetails:
    id: str
    amount_total: int
    currency: str
    payment_status: str
    customer_email: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class CheckoutSessionInfo:
    session: SessionDetails
    email: str
    first_name: str = ''
    last_name: str = ''


def get_checkout_session_info(session_id: str) -> CheckoutSessionInfo:
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        email = session.get('customer_details', {}).get('email', '')
        first_name = session.get('customer_details', {}).get('name', '').split()[0]
        last_name = session.get('customer_details', {}).get('name', '').split()[-1]

        session_details = parse_session_details(session)

        return CheckoutSessionInfo(
            session=session_details,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
    except stripe.error.StripeError as e:
        raise RuntimeError(f"Error retrieving checkout session: {e}")


def get_checkout_event(payload, sig_header, endpoint_secret):
    try:
        return True, stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        return False, "Invalid payload"
    except stripe.error.SignatureVerificationError as e:
        return False, f'Invalid signature: {e}; sig: {sig_header} - secret: {endpoint_secret}'


def parse_session_details(session_data) -> SessionDetails:
    return SessionDetails(
        id=session_data.get('id', ''),
        amount_total=session_data.get('amount_total', 0),
        currency=session_data.get('currency', ''),
        payment_status=session_data.get('payment_status', ''),
        customer_email=session_data.get('customer_details', {}).get('email', ''),
        metadata=session_data.get('metadata', {})
    )
