from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship

from database import db


class Cart(db.Model):
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=db.func.current_timestamp())
    updated_at = Column(DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    guest_id = Column(String, nullable=True)

    # Relations
    items = relationship('CartItem', back_populates='cart', cascade="all, delete-orphan")

    @classmethod
    def get_cart(cls, user_id=None, guest_id=None):
        if user_id:
            return Cart.query.filter_by(user_id=user_id).first()
        elif guest_id:
            return Cart.query.filter_by(guest_id=guest_id).first()
        return None

    @classmethod
    def add_item_to_cart(cls, product_id, quantity, user_id=None, guest_id=None):
        cart = cls.get_cart(user_id, guest_id)
        if not cart:
            cart = Cart(user_id=user_id, guest_id=guest_id)
            db.session.add(cart)

        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)

        db.session.commit()

    @classmethod
    def remove_item_from_cart(cls, product_id, quantity, user_id=None, guest_id=None):
        cart = cls.get_cart(user_id, guest_id)
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

    @classmethod
    def merge_carts(cls, guest_id, user_id):
        session = db.session

        try:
            guest_cart = Cart.query.filter_by(guest_id=guest_id).first()
            if not guest_cart:
                return "Unable to merge carts as no guest cart found"

            user_cart = Cart.query.filter_by(user_id=user_id).first()

            if not user_cart:
                user_cart = Cart(user_id=user_id)
                session.add(user_cart)
                session.commit()

            for guest_item in guest_cart.items:
                user_item = CartItem.query.filter_by(cart_id=user_cart.id, product_id=guest_item.product_id).first()

                if user_item:
                    user_item.quantity += guest_item.quantity
                else:
                    new_item = CartItem(
                        cart_id=user_cart.id,
                        product_id=guest_item.product_id,
                        quantity=guest_item.quantity
                    )
                    session.add(new_item)

            session.delete(guest_cart)
            session.commit()
            return "Cart merged successfully"

        except SQLAlchemyError as _:
            session.rollback()
            return "Database error during merging carts"

        except Exception as _:
            session.rollback()
            return "Unexpected error during merging carts"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "guest_id": self.guest_id,
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
