from dataclasses import dataclass, field
from typing import Optional, List

from flask import Blueprint, jsonify

from payment.stripe_product import get_products, StripeProduct
from utils.main import safe_int

product_blueprint = Blueprint('product', __name__)


@product_blueprint.route('/product', methods=['GET'])
def get_user_profile():
    products_dict = [map_stripe_to_product(prod).__dict__ for prod in get_products()]
    return jsonify({"message": "Products successfully retrieved.", "products": products_dict}), 200


@dataclass
class Product:
    id: str
    created: int
    default_price: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    category: Optional[str] = None
    name: str = ""
    updated: int = 0


def map_stripe_to_product(stripe_product: StripeProduct) -> Product:
    return Product(
        id=stripe_product.id,
        created=stripe_product.created,
        default_price=stripe_product.default_price,
        description=stripe_product.description,
        images=stripe_product.images,
        category=safe_int(stripe_product.metadata.get('categoryId')),
        name=stripe_product.name,
        updated=stripe_product.updated
    )
