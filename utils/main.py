import re

email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


def is_valid_email(email):
    return re.match(email_regex, email)
