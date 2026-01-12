from app.models.poi import POI

def enrich_poi(poi: POI) -> str:
    """
    Convert POI into text for embeddings.
    """
    return f"""
    Name: {poi.name}
    Category: {poi.category}
    Rating: {poi.rating}
    Best for: {poi.category} lovers
    """
