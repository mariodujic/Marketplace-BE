from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship

from database import db


class Cart(db.Model):
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=db.func.current_timestamp())
    updated_at = Column(DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # Relations
    items = relationship('CartItem', back_populates='cart', cascade="all, delete-orphan")

    @classmethod
    def get_cart_by_user_id(cls, user_id):
        cart = Cart.query.filter_by(user_id=user_id).first()
        if cart:
            return cart.to_dict()
        return None

    @classmethod
    def add_item_to_cart(cls, user_id, product_id, quantity):
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)

        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)

        db.session.commit()

    @classmethod
    def remove_item_from_cart(cls, user_id, product_id, quantity):
        cart = cls.query.filter_by(user_id=user_id).first()
        if not cart:
            raise ValueError("Cart not found")

        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

        if not cart_item:
            raise ValueError("Item not found in cart")

        if cart_item.quantity > quantity:
            cart_item.quantity -= quantity
        else:
            db.session.delete(cart_item)

        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CartItem(db.Model):
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('cart.id'), nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    # Relations
    cart = relationship('Cart', back_populates='items')

    def to_dict(self):
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
        }
