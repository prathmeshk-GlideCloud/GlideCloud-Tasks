def retrieve_context(pois):
    """
    Simple retrieval without embeddings or vector DB.
    Uses selected POIs directly as context.
    """
    return "\n".join(
        f"{poi.name} is a {poi.category} place with rating {poi.rating}."
        for poi in pois
    )
