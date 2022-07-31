import re
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from id_providers.utils import list_id_providers, get_id_provider, get_id_provider_by_url, get_entity_by_url
from models import Entity
from sqlmodel import Field, SQLModel, create_engine, Session
import json
import pydantic.json


app = FastAPI()
engine = None


def _custom_json_serializer(*args, **kwargs) -> str:
    """
    Encodes json in the same way that pydantic does.
    """
    return json.dumps(*args, default=pydantic.json.pydantic_encoder, **kwargs)


# @app.on_event("startup")
# async def startup_event():
# connection = 'sqlite:///:memory:?cache=shared'
connection = 'sqlite:////tmp/neo.db'
engine = create_engine(connection, echo=True, json_serializer=_custom_json_serializer,
                       connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine)


def provider_not_found():
    raise HTTPException(status_code=404, detail="Provider not found")


@app.get("/entity_id_providers")
async def supported_id_provider_list():
    ss = map(lambda s: {"name": s.NAME, "wiki_property_id": s.WIKI_PROPERTY_ID},
             list_id_providers())
    return list(ss)


@app.get("/entity_id_by_url")
async def parse_url(url: str = Query(regex="^https?://.+")):
    cls = get_id_provider_by_url(url)
    return cls.parse_url(url) if cls else provider_not_found()
    # return Entity.clone(cls.parse_url(url)) if cls else None


@app.get("/entity_detail_by_url")
async def scrape_url(url: str = Query(regex="^https?://.+")):
    cls = get_id_provider_by_url(url)
    if not cls:
        return provider_not_found()
    entity = cls.scrape(get_entity_by_url(url).id_value)
    with Session(engine) as session:
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity


@app.get("/entity/{id_provider}/{id_value}")
async def get_entity(id_provider: str, id_value: str):
    cls = get_id_provider(id_provider)
    return cls.scrape(id_value) if cls else provider_not_found()


@app.get("/entity/{id_provider}/{id_value}/url")
async def get_entity_url(id_provider: str, id_value: str):
    cls = get_id_provider(id_provider)
    return cls.get_entity(id_value).url if cls else provider_not_found()


@app.get("/entity/{id_provider}/{id_value}/redirect")
async def get_entity_url_redirect(id_provider: str, id_value: str):
    cls = get_id_provider(id_provider)
    return RedirectResponse(cls.get_entity(id_value).url) if cls else provider_not_found()
