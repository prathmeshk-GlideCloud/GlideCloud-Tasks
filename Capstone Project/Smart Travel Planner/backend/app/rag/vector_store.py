import chromadb
from chromadb.utils import embedding_functions
from app.rag.poi_enrichment import enrich_poi

client = chromadb.Client()

collection = client.create_collection(
    name="pois"
)

def store_pois(pois):
    for poi in pois:
        collection.add(
            documents=[enrich_poi(poi)],
            ids=[poi.place_id]
        )
