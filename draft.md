APIs
====
//cat.neodb.social/entity_id_providers
//cat.neodb.social/entity_id_by_url?url={url}
//cat.neodb.social/entity/{provider_name}/{id}/detail
//cat.neodb.social/entity/{provider_name}/{id}/url
//cat.neodb.social/entity/{provider_name}/{id}/redirect
//cat.neodb.social/entity/{provider_name}/{id}/refresh
//cat.neodb.social/search/

Use Cases
=========

user search book by keyword

user search book by url

user search book by ids (ISBN, etc)

user refresh book description

user update book description

user write review for book.external.com/idX on my.neodb.site:
my.neodb.site look up External Site, Key in local cache
my.neodb.site -> cat.neodb.social/extract_url/ url -> External Site, Key
my.neodb.site -> cat.neodb.social/get_external_data/ url -> External Site, Key -> External EntityData, Other [(External Site, Key)]
my.neodb.site save local cache for External EntityData, Site, Key etc
my.neodb.site look up local entity for matching any (External Site, Key) pair
my.neodb.site create new local entity idY
my.neodb.site create new review for local entity idY
my.neodb.site post review to federated sites with external ids. 

user write review for a non-external book on my.neodb.site:

user batch import review 

user edit/delete review

user list reviews for book

user list/add/edit/remove tag

user list/add/edit/remove collection


Global Catalog Service
url -> External Site, Key
External Site, Key -> External EntityData, Other [(External Site, Key)]


Local Catalog Service


Entity
Id
Title
Brief

ExtenralSystems: [(ExternalSystemId, ExternalEntityId, ExternalEntityData), ...]
People:[(Role, Name, Id)]
...

EntityGroup
Type (VideoSeries|BookSeries|Works)

People



https://www.wikidata.org/w/api.php?action=wbsearchentities&search=upc&language=en&type=property

https://book.douban.com/isbn/1234
