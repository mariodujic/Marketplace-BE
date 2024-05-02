import json

from flask import Blueprint, jsonify

from payment.stripe import get_products
from payment.stripe_product import StripeProduct

product = Blueprint('product', __name__)


@product.route('/product', methods=['GET'])
def get_user_profile():
    data = json.loads(get_products())
    print(data)
    products = [StripeProduct(**prod) for prod in data['data']]
    products_dict = [prod.__dict__ for prod in products]
    return jsonify({"message": "Products successfully retrieved.", "products": products_dict}), 200
