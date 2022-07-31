from models import *
from .basic import ISBN10, ISBN13, ASIN
from .external import DoubanMovie, Goodreads, GoogleBook

ID_PROVIDERS = [DoubanMovie, Goodreads, GoogleBook]


def list_id_providers():
    return ID_PROVIDERS


def get_id_provider(id_type: IdType):
    return next(filter(lambda p: p.ID_TYPE == id_type, ID_PROVIDERS), None)


def get_id_provider_by_url(url: str):
    return next(filter(lambda p: p.validate_url(url), ID_PROVIDERS), None)


def get_entity_by_url(url: str):
    p = get_id_provider_by_url(url)
    return p.parse_url(url) if p else None
