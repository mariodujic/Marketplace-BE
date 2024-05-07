import hashlib

from sqlalchemy import Boolean

from database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(15))
    address = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())
    active = db.Column(Boolean, default=True, nullable=False)

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def create_user(cls, email, password):
        new_user = cls(email=email, password_hash=cls.hash_password(password))
        db.session.add(new_user)
        try:
            db.session.commit()
            return new_user
        except Exception as _:
            db.session.rollback()
            return None

    @classmethod
    def verify_user(cls, email, password):
        user = cls.query.filter_by(email=email).first()
        if user and user.password_hash == cls.hash_password(password):
            return True
        return False

    @classmethod
    def user_exists(cls, email):
        return db.session.query(db.exists().where(cls.email == email)).scalar()

    @classmethod
    def get_by_email(cls, email):
        user = cls.query.filter_by(email=email).first()
        return user

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "active": self.active
        }

    def update(self, updates):
        for key, value in updates.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        try:
            if 'password' in updates:
                self.password_hash = self.hash_password(updates['password'])
            db.session.commit()
        except Exception as _:
            db.session.rollback()
            return False
        return True

    @classmethod
    def validate_user_id(cls, user_id, guest_id):
        if not user_id and not guest_id:
            return False, "Either user_id or guest_id is required"

        if user_id:
            try:
                user_id = int(user_id)
            except ValueError:
                return False, "Invalid user_id format"

            user = User.query.filter_by(id=user_id).first()
            if not user:
                return False, "User does not exist"

        if guest_id and (not isinstance(guest_id, str) or guest_id.strip() == ""):
            return False, "Invalid guest_id format"

        return True, None
