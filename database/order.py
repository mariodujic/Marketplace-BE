import enum

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Float
from sqlalchemy.orm import relationship

from database import db


class OrderStatus(enum.Enum):
    PENDING = 'pending'
    PAID = 'paid'
    CANCELLED = 'cancelled'


class Order(db.Model):
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('cart.id'), nullable=True, unique=False)
    created_at = Column(DateTime, server_default=db.func.current_timestamp())
    updated_at = Column(DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    guest_id = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False, default=0.0)  # In cents
    status = Column(String, nullable=False, default=OrderStatus.PENDING.value)

    # Relations
    cart = relationship('Cart', back_populates='order')
    items = relationship('OrderItem', back_populates='order', cascade="all, delete-orphan")

    @classmethod
    def get_order(cls, order_id, user_id=None, guest_id=None):
        query = Order.query.filter_by(id=order_id)

        if user_id:
            query = query.filter_by(user_id=user_id)
        elif guest_id:
            query = query.filter_by(guest_id=guest_id)

        if query.count() == 0:
            return False, "Order does not exist"
        return True, query.first()

    @classmethod
    def create_order(cls, cart_id, user_id=None, guest_id=None):
        try:
            query = Order.query.filter_by(cart_id=cart_id).first()
            if query and query.status == OrderStatus.PAID.value:
                return False, "Cart is already linked to an existing paid order"

            order = cls(user_id=user_id, guest_id=guest_id, cart_id=cart_id)
            db.session.add(order)
            db.session.commit()
            return True, order
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to create order: {str(e)}"

    @classmethod
    def get_order_by_cart_id_for_status(cls, cart_id, status):
        try:
            order = Order.query.filter_by(cart_id=cart_id, status=status)
            if order.count() > 0:
                return True, order.first()
            else:
                return False, "No order linked to this cart"
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to retrieve order: {str(e)}"

    @classmethod
    def add_item_to_order(cls, order_id, product_id, quantity, price, currency):
        order = cls.query.get(order_id)
        if not order:
            return False, "Order not found"

        order_item = OrderItem.query.filter_by(order_id=order.id, product_id=product_id).first()
        if order_item:
            order_item.quantity += quantity
            order_item.price = price
            order_item.currency = currency
        else:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                price=price,
                currency=currency
            )
            db.session.add(order_item)

        order.total_amount += quantity * price
        db.session.commit()

        return True, "Item successfully added to order"

    @classmethod
    def update_order_status(cls, order_id, new_status):
        try:
            new_status_enum = OrderStatus[new_status.upper()]
        except KeyError:
            return False, f"Invalid order status: {new_status}"

        order = cls.query.get(order_id)
        if not order:
            return False, "Order not found"

        order.status = new_status_enum.value
        db.session.commit()

        return True, "Order updated"

    def update_total_amount(self, total_amount):
        self.total_amount = total_amount
        db.session.commit()

    @classmethod
    def cancel_order(cls, order_id):
        return cls.update_order_status(order_id, OrderStatus.CANCELLED.value)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "guest_id": self.guest_id,
            "total_amount": self.total_amount,  # In cents
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class OrderItem(db.Model):
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('order.id'), nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Integer, nullable=False, default=0.0)
    currency = Column(String, nullable=False, default="eur")

    # Relations
    order = relationship('Order', back_populates='items')

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": self.price,  # In cents
            "currency": self.currency
        }
