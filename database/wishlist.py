from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship

from database import db


class Wishlist(db.Model):
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=db.func.current_timestamp())
    updated_at = Column(DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=True)

    # Relations
    items = relationship('WishlistItem', back_populates='wishlist', cascade="all, delete-orphan")

    @classmethod
    def get_wishlist(cls, user_id=None):
        if user_id:
            return cls.query.filter_by(user_id=user_id).first()
        return None

    @classmethod
    def add_item_to_wishlist(cls, product_id, user_id=None):
        wishlist = cls.get_wishlist(user_id)

        if not wishlist:
            wishlist = Wishlist(user_id=user_id)
            db.session.add(wishlist)

        wishlist_item = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
        if not wishlist_item:
            wishlist_item = WishlistItem(wishlist_id=wishlist.id, product_id=product_id)
            db.session.add(wishlist_item)

        db.session.commit()

    @classmethod
    def remove_item_from_wishlist(cls, product_id, user_id=None):
        wishlist = cls.get_wishlist(user_id)
        if not wishlist:
            return False, "Wishlist not found"

        wishlist_item = WishlistItem.query.filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
        if not wishlist_item:
            return False, "Item not found in wishlist"

        db.session.delete(wishlist_item)
        db.session.commit()
        return True, "Successfully removed item from wishlist"


class WishlistItem(db.Model):
    id = Column(Integer, primary_key=True)
    wishlist_id = Column(Integer, ForeignKey('wishlist.id'), nullable=False)
    product_id = Column(String, nullable=False)

    # Relations
    wishlist = relationship('Wishlist', back_populates='items')

    def to_dict(self):
        return {
            "id": self.id,
            "wishlist_id": self.wishlist_id,
            "product_id": self.product_id,
        }
