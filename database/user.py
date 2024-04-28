import hashlib

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
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {e}")
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
