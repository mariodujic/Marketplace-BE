import os
from dataclasses import dataclass
from typing import Dict, List, Any

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
    object: str
    amount_subtotal: int
    amount_total: int
    automatic_tax: Dict[str, Any]
    cancel_url: str
    client_reference_id: str
    currency: str
    customer: str
    customer_details: Dict[str, Any]
    customer_email: str
    locale: str
    metadata: Dict[str, str]
    mode: str
    payment_intent: str
    payment_method_options: Dict[str, Any]
    payment_method_types: List[str]
    payment_status: str
    setup_intent: str
    shipping_address: str
    submit_type: str
    success_url: str
    total_details: Dict[str, Any]
    url: str


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
    shipping_address = session_data.get('shipping_details', {}).get('address', {})
    shipping_address_formatted = ', '.join(filter(None, [
        shipping_address.get('line1', ''),
        shipping_address.get('line2', ''),
        shipping_address.get('city', ''),
        shipping_address.get('state', ''),
        shipping_address.get('postal_code', ''),
        shipping_address.get('country', '')
    ]))
    return SessionDetails(
        id=session_data.get('id', ''),
        object=session_data.get('object', ''),
        amount_subtotal=session_data.get('amount_subtotal', 0),
        amount_total=session_data.get('amount_total', 0),
        automatic_tax=session_data.get('automatic_tax', {}),
        cancel_url=session_data.get('cancel_url', ''),
        client_reference_id=session_data.get('client_reference_id', ''),
        currency=session_data.get('currency', ''),
        customer=session_data.get('customer', ''),
        customer_details=session_data.get('customer_details', {}),
        customer_email=session_data.get('customer_details', {}).get('email', ''),
        locale=session_data.get('locale', ''),
        metadata=session_data.get('metadata', {}),
        mode=session_data.get('mode', ''),
        payment_intent=session_data.get('payment_intent', ''),
        payment_method_options=session_data.get('payment_method_options', {}),
        payment_method_types=session_data.get('payment_method_types', []),
        payment_status=session_data.get('payment_status', ''),
        setup_intent=session_data.get('setup_intent', ''),
        shipping_address=shipping_address_formatted,
        submit_type=session_data.get('submit_type', ''),
        success_url=session_data.get('success_url', ''),
        total_details=session_data.get('total_details', {}),
        url=session_data.get('url', '')
    )
