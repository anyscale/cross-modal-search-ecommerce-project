import typer
import os

import ray
from pinecone import Pinecone, ServerlessSpec


@ray.remote
def setup_pinecone(index_name: str, vector_dim: int) -> None:
    try:
        api_key = os.environ["PINECONE_API_KEY"]
    except KeyError:
        typer.echo(
            "Pinecone API key not found. Set it using environment variable PINECONE_API_KEY."
        )
        raise

    pc = Pinecone(api_key=api_key)
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=vector_dim,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=os.environ.get("PINECONE_CLOUD", "aws"),
                region=os.environ.get("PINECONE_REGION", "us-east-1"),
            ),
        )
