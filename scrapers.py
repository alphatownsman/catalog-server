import re
import settings
from langdetect import detect
from downloader import *
from models import *
from id_providers.basic import standard_book_id_to_entity

RE_NUMBERS = re.compile(r"\d+")
RE_WHITESPACES = re.compile(r"\s+")


class ParseError(Exception):
    def __init__(self, scraper, field):
        msg = f'{type(scraper).__name__}: Error parsing field "{field}" for url {scraper.url}'
        super().__init__(msg)


class BaseScraper:
    def __init__(self, entity, response=None):
        self.entity = entity
        self.url = entity.url
        self.response = response
        self.cover_image = None
        self.cover_image_extension = None
        self.data = {}
        self.ids = []
        self.credits = []
        self.dates = []
        self.title = []

    def get_html(self):
        if self.response is not None:
            content = self.response.content
        else:
            dl = ProxiedDownloader(self.url)
            content = dl.download().content
            # with open('/tmp/temp.html', 'w', encoding='utf-8') as fp:
            #     fp.write(content.decode('utf-8'))
        return html.fromstring(content.decode('utf-8'))

    def set_field(self, field, value=None):
        self.data[field] = value

    def parse_str(self, query):
        elem = self.html.xpath(query)
        return elem[0].strip() if elem else None

    def parse_field(self, field, query, error_when_missing=False):
        elem = self.html.xpath(query)
        if elem:
            self.data[field] = elem[0].strip()
        elif error_when_missing:
            raise ParseError(self, field)
        else:
            self.data[field] = None


class GoodreadsScraper(BaseScraper):
    def scrape(self):
        self.html = self.get_html()
        # this breaks occationally when goodreads returns a react/responsive version
        self.parse_field("title", "//h1[@id='bookTitle']/text()", error_when_missing=True)
        self.title.append(LocalizedString(lang=detect(self.data['title']), s=self.data['title']))
        self.set_field("subtitle")
        self.parse_field("orig_title", "//div[@id='bookDataBox']//div[text()='Original Title']/following-sibling::div/text()")
        self.parse_field("language", '//div[@itemprop="inLanguage"]/text()')
        self.parse_field("binding", '//span[@itemprop="bookFormat"]/text()')
        for query in ['//span[@itemprop="isbn"]/text()', '//div[@itemprop="isbn"]/text()', "//div[text()='ISBN']/following-sibling::div/text()"]:
            isbn_or_asin = standard_book_id_to_entity(self.parse_str(query))
            if isbn_or_asin:
                self.ids.append(isbn_or_asin)
        self.parse_field("genre", '//div[@class="bigBoxBody"]/div/div/div/a/text()')
        self.parse_field("cover_image_url", "//img[@id='coverImage']/@src")

        if self.data["cover_image_url"]:
            imgdl = BasicImageDownloader(self.data["cover_image_url"], self.url)
            self.cover_image = imgdl.download().content
            self.cover_image_extention = imgdl.extention

        try:
            months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            r = re.compile('.*Published.*(' + '|'.join(months) + ').*(\\d\\d\\d\\d).+by\\s*(.+)\\s*', re.DOTALL)
            pub = r.match(self.parse_str("//div[contains(text(), 'Published') and @class='row']/text()"))
            year = int(pub[2])
            month = months.index(pub[1])+1
            # TODO parse day
            self.dates.append(HistoricalDate(date_type=DateType.Publish, sortable_date=date(year, month, 1), year=year, month=month, day=None))
            self.credits.append(Credit(role=Role.Publisher, name=pub[3].strip()))
        except Exception:
            pass

        try:
            pub = re.match(r'.*first published\s+(.+\d\d\d\d).*', self.parse_str("//nobr[contains(text(), 'first published')]/text()"), re.DOTALL)
            year = int(pub[1])
            self.dates.append(HistoricalDate(date_type=DateType.FirstPublish, sortable_date=date(year, 1, 1), year=year, month=None, day=None))
        except Exception:
            pass

        self.parse_field("pages", '//span[@itemprop="numberOfPages"]/text()')
        if self.data['pages'] is not None:
            self.data['pages'] = int(RE_NUMBERS.findall(self.data['pages'])[0]) if RE_NUMBERS.findall(self.data['pages']) else None

        brief_elem = self.html.xpath('//div[@id="description"]/span[@style="display:none"]/text()')
        if brief_elem:
            self.data['brief'] = '\n'.join(p.strip() for p in brief_elem)
        else:
            brief_elem = self.html.xpath('//div[@id="description"]/span/text()')
            self.data['brief'] = '\n'.join(p.strip() for p in brief_elem) if brief_elem else None

        authors_elem = self.html.xpath("//a[@class='authorName'][not(../span[@class='authorName greyText smallText role'])]/span/text()")
        if authors_elem:
            for author in authors_elem:
                self.credits.append(Credit(role=Role.Author, name=RE_WHITESPACES.sub(' ', author.strip())))

        authors_elem = self.html.xpath("//a[@class='authorName'][../span/text()='(Translator)']/span/text()")
        if authors_elem:
            for translator in authors_elem:
                self.credits.append(Credit(role=Role.Translater, name=RE_WHITESPACES.sub(' ', author.strip())))

        # TODO parse secondary ISBN
        #   http://127.0.0.1:8000/entity/Goodreads/5211
        #   http://127.0.0.1:8000/entity/Goodreads/35825012
        # TODO parse serie and work id 
        #   http://127.0.0.1:8000/entity/Goodreads/35825012
        series_elem = self.html.xpath("//h2[@id='bookSeries']/a/text()")
        if series_elem:
            self.data['series'] = re.sub(r'\(\s*(.+[^\s])\s*#.*\)', '\\1', series_elem[0].strip())


class GoogleBookScraper(BaseScraper):
    def scrape(self):
        api_url = f'https://www.googleapis.com/books/v1/volumes/{self.entity.id_value}'
        dl = BasicDownloader(api_url)
        resp = dl.download()
        b = resp.json()
        if 'title' not in b['volumeInfo']:
            raise ParseError(self, 'title')
        self.title.append(LocalizedString(lang=detect(b['volumeInfo']['title']), s=b['volumeInfo']['title']))
        self.data['subtitle'] = b['volumeInfo']['subtitle'] if 'subtitle' in b['volumeInfo'] else None
        if 'publishedDate' in b['volumeInfo']:
            pub_date = b['volumeInfo']['publishedDate'].split('-')
            year = int(pub_date[0])
            month = int(pub_date[1]) if len(pub_date) > 1 else None
            day = int(pub_date[2]) if len(pub_date) > 2 else None
            self.dates.append(HistoricalDate(date_type=DateType.Publish, sortable_date=date(year, month if month else 1, day if day else 1), year=year, month=month, day=day))
        if 'publisher' in b['volumeInfo']:
            self.credits.append(Credit(role=Role.Publisher, name=b['volumeInfo']['publisher']))
        self.data['language'] = b['volumeInfo']['language'] if 'language' in b['volumeInfo'] else None
        self.data['pages'] = b['volumeInfo']['pageCount'] if 'pageCount' in b['volumeInfo'] else None
        if 'mainCategory' in b['volumeInfo']:
            self.data['genre'] = b['volumeInfo']['mainCategory']
        if 'authors' in b['volumeInfo']:
            for a in b['volumeInfo']['authors']:
                self.credits.append(Credit(role=Role.Author, name=a))
        if 'description' in b['volumeInfo']:
            self.data['brief'] = b['volumeInfo']['description']
        elif 'textSnippet' in b['volumeInfo']:
            self.data['brief'] = b["volumeInfo"]["textSnippet"]["searchInfo"]
        else:
            self.data['brief'] = ''
        self.data['brief'] = re.sub(r'<.*?>', '', self.data['brief'].replace('<br', '\n<br'))

        self.data["cover_image_url"] = b['volumeInfo']['imageLinks']['thumbnail'] if 'imageLinks' in b['volumeInfo'] else None
        imgdl = BasicImageDownloader(self.data["cover_image_url"], self.url)
        try:
            self.cover_image = imgdl.download().content
            self.cover_image_extention = imgdl.extention
        except Exception:
            pass
        for iid in b['volumeInfo']['industryIdentifiers'] if 'industryIdentifiers' in b['volumeInfo'] else []:
            isbn_or_asin = standard_book_id_to_entity(iid['identifier'])  # iid['type'] == 'ISBN_10' / 'ISBN_13' / 'ISSN'
            if isbn_or_asin:
                self.ids.append(isbn_or_asin)
