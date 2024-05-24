from dataclasses import dataclass, field
from typing import Optional, List

from flask import Blueprint, jsonify, request

from payment.stripe_product import StripeProduct, get_all_product_category_ids, get_stripe_products
from utils.common import safe_int
from utils.constants import ResponseKey
from utils.limiter import limiter

product_blueprint = Blueprint('product', __name__)


@product_blueprint.route('/products/categories', methods=['GET'])
@limiter.limit("400/minute")
def get_product_categories():
    categories = get_all_product_category_ids()
    return jsonify({ResponseKey.MESSAGE.value: "Categories successfully retrieved.", "categories": categories}), 200


@product_blueprint.route('/products', methods=['GET'])
@limiter.limit("400/minute")
def get_products():
    category_id = request.args.get('category_id')
    featured = request.args.get('featured') == 'true'
    product_ids = request.args.getlist('id')

    all_products = get_stripe_products()

    filtered_products = []
    if product_ids:
        filtered_products = [map_stripe_to_product(product) for product in all_products if product.id in product_ids]
    else:
        for product in all_products:
            if category_id and safe_int(product.metadata.get('category_id')) != safe_int(category_id):
                continue

            if featured and product.metadata.get('featured') != 'true':
                continue

            filtered_products.append(map_stripe_to_product(product))

    return jsonify(
        {
            ResponseKey.MESSAGE.value: "Products successfully retrieved.",
            "products": filtered_products
        }
    ), 200


@dataclass
class Product:
    id: str
    created: int
    default_price: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    category_id: Optional[str] = None
    in_stock: Optional[bool] = None
    name: str = ""
    updated: int = 0


def map_stripe_to_product(stripe_product: StripeProduct) -> Product:
    return Product(
        id=stripe_product.id,
        created=stripe_product.created,
        default_price=stripe_product.default_price,
        description=stripe_product.description,
        images=stripe_product.images,
        category_id=safe_int(stripe_product.metadata.get('category_id')),
        in_stock=stripe_product.metadata.get('in_stock') == 'true' if 'in_stock' in stripe_product.metadata else False,
        name=stripe_product.name,
        updated=stripe_product.updated
    )
