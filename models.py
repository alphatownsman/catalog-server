# from pydantic import BaseModel, Field
from enum import Enum
from datetime import date
from sqlmodel import Field, SQLModel, Column, JSON


class NeoModel(SQLModel):
    @classmethod
    def clone(self, object):
        return self(**object.dict())


class LocalizedString(NeoModel):
    lang: str
    s: str


String = list[LocalizedString]


class IdType(str, Enum):
    WikiData = 'wikidata'
    ISBN10 = 'isbn10'
    ISBN13 = 'isbn13'
    ASIN = 'asin'
    ISSN = 'issn'
    CUBN = 'cubn'  # Chinese Unifed Book Number
    ISRC = 'isrc'
    GTIN = 'gtin'  # aka UPC, UCC, EAN
    IMDb = 'imdb'
    TMDB_TV = 'tmdb_tv'
    TMDB_Movie = 'tmdb_movie'
    Goodreads = 'goodreads'
    Goodreads_Work = 'goodreads_work'
    GoogleBook = 'googlebook'
    DoubanBook = 'doubanbook'
    DoubanBook_Work = 'doubanbook_work'
    DoubanMovie = 'doubanmovie'
    DoubanMusic = 'doubanmusic'
    DoubanGame = 'doubangame'
    DoubanDrama = 'doubandrama'
    Bandcamp = 'bandcamp'
    Spotify_Album = 'spotify_album'
    DoubanBook_Author = 'doubanbook_author'
    DoubanCelebrity = 'doubanmovie_celebrity'
    Goodreads_Author = 'goodreads_author'
    Spotify_Artist = 'spotify_artist'
    TMDB_Person = 'tmdb_person'


class Entity(SQLModel):
    id_type: IdType
    id_value: str


class Role(str, Enum):
    Author = 'author'
    Translater = 'translator'
    Director = 'director'
    Actor = 'actor'
    Publisher = 'publisher'


class Contributor(NeoModel):
    id_type: IdType | None = Field(default=None)
    id_value: str | None = Field(default=None)
    name: str


class Credit(Contributor):
    role: Role


class DateType(str, Enum):
    FirstPublish = 'first_publish'
    Publish = 'publish'
    Release = 'release'
    FirstAir = 'first_air'


class HistoricalDate(NeoModel):
    date_type: DateType
    sortable_date: date
    year: int
    month: int|None = Field(default=None)
    day: int|None = Field(default=None)


class ExternalEntity(Entity, table=True):
    id: int|None = Field(default=None, primary_key=True)
    url: str
    title: String = Field(default=[], sa_column=Column(JSON))
    data: dict = Field(default={}, sa_column=Column(JSON))
    ids: list[Entity] = Field(default=[], sa_column=Column(JSON))
    credits: list[Credit] = Field(default=[], sa_column=Column(JSON))
    dates: list[HistoricalDate] = Field(default=[], sa_column=Column(JSON))

    class Config:
        arbitrary_types_allowed = True  # Needed for Column(JSON)