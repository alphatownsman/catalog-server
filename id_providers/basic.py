import re
from models import *


class BasicIdProvider:
    ID_TYPE:IdType

    @classmethod
    def validate(self, id_value: str|None):
        return len(id_value.strip())>0 if id_value is not None else False

    @classmethod
    def normalize(self, id_value: str):
        return id_value.strip().upper()

    @classmethod
    def get_entity(self, id_value: str):
        return Entity(id_type=self.ID_TYPE, id_value=self.normalize(id_value))


class GTIN(BasicIdProvider):
    ID_TYPE: IdType = IdType.GTIN

    @classmethod
    def validate(self, id_value: str|None):
        if id_value is None:
            return False
        v = GTIN.normalize(id_value)
        return re.match(r'^[0-9\-]{7,12}[0-9xX]$', v) if id_value is not None else False


class ISBN10(BasicIdProvider):
    ID_TYPE: IdType = IdType.ISBN10

    @classmethod
    def validate(self, id_value: str|None):
        return re.match(r'^[0-9]{9}[0-9xX]$', id_value.strip()) if id_value is not None else False


class ISBN13(BasicIdProvider):
    ID_TYPE: IdType = IdType.ISBN13

    @classmethod
    def validate(self, id_value: str|None):
        return re.match(r'^(978|979)[0-9]{9}[0-9xX]$', id_value.strip()) if id_value is not None else False


class ASIN(BasicIdProvider):
    ID_TYPE: IdType = IdType.ASIN

    @classmethod
    def validate(self, id_value: str|None):
        return re.match(r'^B[0-9A-Za-z]{9}$', id_value.strip()) if id_value is not None else False

    @classmethod
    def normalize(self, id_value: str):
        return id_value.strip().upper()


class ISSN(BasicIdProvider):
    ID_TYPE: IdType = IdType.ISSN

    @classmethod
    def validate(self, id_value: str|None):
        return re.match(r'^[0-9]{4}-[0-9]{3}[0-9xX]$', id_value.strip()) if id_value is not None else False


STANDARD_BOOK_ID_PROVIDERS = [ISBN10, ISBN13, ISSN, ASIN]


def standard_book_id_to_entity(id_value:str):
    id_provider = next(filter(lambda p: p.validate(id_value), STANDARD_BOOK_ID_PROVIDERS), None)
    return id_provider.get_entity(id_value) if id_provider else None
