import re
from models import *
from scrapers import *
from .basic import *


class ExternalIdProvider(BasicIdProvider):
    @classmethod
    def validate_url(self, url: str):
        return False

    @classmethod
    def parse_url(self, url: str):
        return None

    @classmethod
    def get_entity(self, id_value: str):
        return ExternalEntity(id_type=self.ID_TYPE, id_value=self.normalize(id_value), url=self.get_url(id_value))

    @classmethod
    def scrape(self, id_value: str):
        entity = self.get_entity(id_value)
        scraper = self.SCRAPER_CLASS(entity)
        scraper.scrape()
        entity.data = scraper.data
        entity.ids =  scraper.ids
        entity.title = scraper.title
        entity.credits = scraper.credits
        entity.dates = scraper.dates
        return entity


class DoubanMovie(ExternalIdProvider):
    ID_TYPE = IdType.DoubanMovie
    WIKI_PROPERTY_ID = 'P4529'


class Goodreads(ExternalIdProvider):
    ID_TYPE = IdType.Goodreads
    WIKI_PROPERTY_ID = 'P2968'
    SCRAPER_CLASS = GoodreadsScraper

    @classmethod
    def get_url(self, id_value):
        return "https://www.goodreads.com/book/show/" + id_value

    @classmethod
    def validate_url(self, url: str):
        u = re.match(r".+/book/show/(\d+)", url)
        if not u:
            u = re.match(r".+book/(\d+)", url)
        return u is not None

    @classmethod
    def parse_url(self, url: str):
        u = re.match(r".+/book/show/(\d+)", url)
        if not u:
            u = re.match(r".+book/(\d+)", url)
        return self.get_entity(u[1]) if u else None


class GoogleBook(ExternalIdProvider):
    ID_TYPE = IdType.GoogleBook
    WIKI_PROPERTY_ID = 'P675'
    SCRAPER_CLASS = GoogleBookScraper

    @classmethod
    def normalize(self, id_value: str):
        return id_value.strip()

    @classmethod
    def get_url(self, id_value):
        return "https://books.google.com/books?id=" + id_value

    @classmethod
    def validate_url(self, url: str):
        u = re.match(r"https://books\.google\.com/books.*id=([^&#]+)", url)
        if not u:
            u = re.match(r"https://www\.google\.com/books/edition/[^/]+/([^&#?]+)", url)
        return u is not None

    @classmethod
    def parse_url(self, url: str):
        u = re.match(r"https://books\.google\.com/books.*id=([^&#]+)", url)
        if not u:
            u = re.match(r"https://www\.google\.com/books/edition/[^/]+/([^&#?]+)", url)
        return self.get_entity(u[1]) if u else None
