import json
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict

import stripe


@dataclass
class StripePrice:
    id: str
    unit_amount: int
    currency: str


@dataclass
class StripeProduct:
    id: str
    object: str
    active: bool
    created: int
    default_price: Optional[StripePrice] = None
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    livemode: bool = False
    attributes: List[str] = field(default_factory=list)
    marketing_features: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    name: str = ""
    package_dimensions: Optional[dict] = None
    shippable: Optional[bool] = None
    statement_descriptor: Optional[str] = None
    tax_code: Optional[str] = None
    unit_label: Optional[str] = None
    type: Optional[str] = None
    updated: int = 0
    url: Optional[str] = None


# Time-to-Live in seconds
# 15 min
_ttl = 900


@dataclass
class ProductCache:
    cache: List[StripeProduct] = field(default_factory=list)
    cache_expiration_time: float = field(default_factory=lambda: time.time() + _ttl)

    def is_expired(self):
        return time.time() > self.cache_expiration_time

    def update_cache(self, new_cache):
        self.cache = new_cache
        self.cache_expiration_time = time.time() + _ttl

    def get_product_by_id(self, product_id: str) -> Optional[StripeProduct]:
        for product in self.cache:
            if product.id == product_id:
                return product
        return None


_product_cache = ProductCache()


# Stripe doc reference: https://stripe.com/docs/api/products/list, https://docs.stripe.com/api/prices/retrieve
def get_stripe_products():
    global _product_cache
    if _product_cache.cache and not _product_cache.is_expired():
        return _product_cache.cache

    products_response = stripe.Product.list(limit=100)
    products_json = json.dumps(products_response)
    data = json.loads(products_json)
    products = []

    for prod in data['data']:
        default_price_id = prod.get('default_price')
        default_price_data = None

        if default_price_id:
            default_price = stripe.Price.retrieve(default_price_id)
            default_price_data = StripePrice(
                id=default_price.id,
                unit_amount=default_price.unit_amount,
                currency=default_price.currency
            )
        product = StripeProduct(
            id=prod['id'],
            object=prod['object'],
            active=prod['active'],
            created=prod['created'],
            default_price=default_price_data,
            description=prod.get('description'),
            images=prod.get('images', []),
            features=prod.get('features', []),
            livemode=prod.get('livemode', False),
            attributes=prod.get('attributes', []),
            marketing_features=prod.get('marketing_features', []),
            metadata=prod.get('metadata', {}),
            name=prod['name'],
            package_dimensions=prod.get('package_dimensions'),
            shippable=prod.get('shippable'),
            statement_descriptor=prod.get('statement_descriptor'),
            tax_code=prod.get('tax_code'),
            unit_label=prod.get('unit_label'),
            type=prod.get('type'),
            updated=prod['updated'],
            url=prod.get('url')
        )
        products.append(product)
    _product_cache.update_cache(products)
    return products


def get_cached_product_by_id(product_id: str) -> Optional[StripeProduct]:
    global _product_cache
    if _product_cache.is_expired():
        get_stripe_products()
    return _product_cache.get_product_by_id(product_id)


def get_all_product_category_ids():
    products = get_stripe_products()
    category_ids = {product.metadata['category_id'] for product in products if 'category_id' in product.metadata}
    return list(category_ids)
