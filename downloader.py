import requests
import re
import filetype
from lxml import html
from PIL import Image
from io import BytesIO
import settings
from requests.exceptions import RequestException


RESPONSE_OK = 0  # response is ready for pasring
RESPONSE_INVALID_CONTENT = -1  # content not valid but no need to retry
RESPONSE_NETWORK_ERROR = -2  # network error, retry next proxied url
RESPONSE_CENSORSHIP = -3  # censored, try sth special if possible


class DownloadError(Exception):
    def __init__(self, downloader):
        self.url = downloader.url
        self.logs = downloader.logs
        if downloader.response_type == RESPONSE_INVALID_CONTENT:
            error = "Invalid Response"
        elif downloader.response_type == RESPONSE_NETWORK_ERROR:
            error = "Network Error"
        elif downloader.response_type == RESPONSE_NETWORK_ERROR:
            error = "Censored Content"
        else:
            error = "Unknown Error"
        self.message = f"Download Failed: {error}, url: {self.url}"
        super().__init__(self.message)


class BasicDownloader:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:70.0) Gecko/20100101 Firefox/70.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
    }

    def __init__(self, url):
        self.url = url
        self.response_type = RESPONSE_OK
        self.logs = []

    def get_timeout(self):
        return settings.SCRAPING_TIMEOUT

    def validate_response(self, response):
        if response is None:
            return RESPONSE_NETWORK_ERROR
        elif response.status_code != 200:
            return RESPONSE_INVALID_CONTENT
        else:
            return RESPONSE_OK

    def _download(self, url):
        try:
            resp = requests.get(self.url, headers=self.headers, timeout=self.get_timeout())
            response_type = self.validate_response(resp)
            self.logs.append({'response_type': response_type, 'url': url, 'exception': None})
            return resp, response_type
        except RequestException as e:
            self.logs.append({'response_type': RESPONSE_NETWORK_ERROR, 'url': url, 'exception': e})
            return None, RESPONSE_NETWORK_ERROR

    def download(self):
        resp, self.response_type = self._download(self.url)
        if self.response_type == RESPONSE_OK:
            return resp
        else:
            raise DownloadError(self)


class ProxiedDownloader(BasicDownloader):
    def get_proxied_urls(self):
        urls = []
        if settings.SCRAPESTACK_KEY is not None:
            urls.append(f'http://api.scrapestack.com/scrape?access_key={settings.SCRAPESTACK_KEY}&url={self.url}')
        if settings.PROXYCRAWL_KEY is not None:
            urls.append(f'https://api.proxycrawl.com/?token={settings.PROXYCRAWL_KEY}&url={self.url}')
        if settings.SCRAPERAPI_KEY is not None:
            urls.append(f'http://api.scraperapi.com/?api_key={settings.SCRAPERAPI_KEY}&url={self.url}')
        return urls

    def get_special_proxied_url(self):
        return f'{settings.LOCAL_PROXY}?url={self.url}' if settings.LOCAL_PROXY is not None else None

    def download(self):
        urls = self.get_proxied_urls()
        last_try = False
        url = urls.pop(0) if len(urls) else None
        resp = None
        while url:
            resp, resp_type = self._download(url)
            if resp_type == RESPONSE_OK or resp_type == RESPONSE_INVALID_CONTENT or last_try:
                url = None
            elif resp_type == RESPONSE_CENSORSHIP:
                url = self.get_special_proxied_url()
                last_try = True
            else:  # resp_type == RESPONSE_NETWORK_ERROR:
                url = urls.pop(0) if len(urls) else None
        self.response_type = resp_type
        if self.response_type == RESPONSE_OK:
            return resp
        else:
            raise DownloadError(self)


class ImageDownloaderMixin:
    def __init__(self, url, referer=None):
        if referer is not None:
            self.headers['Referer'] = referer
        super().__init__(url)

    def validate_response(self, response):
        if response and response.status_code == 200:
            try:
                raw_img = response.content
                img = Image.open(BytesIO(raw_img))
                img.load()  # corrupted image will trigger exception
                content_type = response.headers.get('Content-Type')
                self.extention = filetype.get_type(mime=content_type.partition(';')[0].strip()).extension
                return RESPONSE_OK
            except Exception:
                return RESPONSE_NETWORK_ERROR
        if response and response.status_code >= 400 and response.status_code < 500:
            return RESPONSE_INVALID_CONTENT
        else:
            return RESPONSE_NETWORK_ERROR


class BasicImageDownloader(ImageDownloaderMixin, BasicDownloader):
    pass


class ProxiedImageDownloader(ImageDownloaderMixin, ProxiedDownloader):
    pass
