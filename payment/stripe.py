import os

import stripe

_base_url = "https://api.stripe.com"


def initialize_stripe():
    stripe.api_key = os.getenv('STRIPE_SK')
