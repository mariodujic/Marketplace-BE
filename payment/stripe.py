import json
import os

import stripe

_base_url = "https://api.stripe.com"


def initialize_stripe():
    stripe.api_key = os.getenv('STRIPE_SK')


# Stripe doc reference: https://stripe.com/docs/api/products/list
def get_products():
    products = stripe.Product.list(limit=100)
    return json.dumps(products)
