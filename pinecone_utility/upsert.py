import os

from pinecone import Pinecone


class UpsertVectors:
    def __init__(self, index_name: str, namespace: str):
        self.pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        self.index = self.pc.Index(index_name)
        self.namespace = namespace

    def __call__(self, batch: dict) -> dict:
        self.index.upsert(
            vectors=[
                {
                    "id": id_,
                    "values": values,
                }
                for id_, values in zip(batch["id"], batch["values"])
            ],
            namespace=self.namespace,
        )
        return batch