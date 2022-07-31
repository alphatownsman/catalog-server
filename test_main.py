from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_entity_id_by_url():
    response = client.get("/entity_id_by_url?url=https://www.goodreads.com/book/show/37836929-")
    assert response.status_code == 200
    assert response.json() == {'credits': [], 'data': {}, 'dates': [], 'id': None, 'id_type': 'goodreads', 'id_value': '37836929', 'ids': [], 'title': [], 'url': 'https://www.goodreads.com/book/show/37836929'}


def test_entity_detail_by_url():
    response = client.get("/entity_detail_by_url?url=https://www.goodreads.com/book/show/37836929-")
    assert response.status_code == 200
    r = response.json()
    r['id'] = 42
    r['data']['brief'] = '...'
    assert r == {'credits': [{'id_type': None, 'id_value': None, 'name': 'Fernando Pessoa', 'role': 'author'}], 'data': {'binding': 'Paperback', 'brief': '...', 'cover_image_url': 'https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1515198677l/37836929._SX318_.jpg', 'genre': 'Fiction', 'language': 'Spanish', 'orig_title': 'Livro do Desassossego por Bernardo Soares', 'pages': 162, 'subtitle': None, 'title': 'Libro del desasosiego'}, 'dates': [], 'id': 42, 'id_type': 'goodreads', 'id_value': '37836929', 'ids': [{'id_type': 'isbn13', 'id_value': '9786079604516'}, {'id_type': 'isbn10', 'id_value': '0141183047'}], 'title': [{'lang': 'es', 's': 'Libro del desasosiego'}], 'url': 'https://www.goodreads.com/book/show/37836929'}
