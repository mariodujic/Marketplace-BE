from enum import Enum


class ResponseKey(Enum):
    MESSAGE: str = "message"
    ERROR: str = "error"
    ACCESS_TOKEN: str = "access_token"
    REFRESH_TOKEN: str = "refresh_token"
    CART_MESSAGE: str = "cart_message"
    CART_ERROR: str = "cart_error"
    ORDER_ID: str = "order_id"
    TOTAL_AMOUNT: str = "total_amount"
    CURRENCY: str = "currency"
