from enum import Enum


class Environment(Enum):
    Dev = 'development'
    Prod = 'production'


def get_environment_file(environment: str):
    if environment == Environment.Dev.value:
        return '.env.development'
    else:
        return '.env.production'
