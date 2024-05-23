from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
from typing import Any, Dict, List

import numpy as np
from fastapi import FastAPI
from PIL import Image
from pinecone import Pinecone
from pydantic import BaseModel
from ray import serve
from ray.serve.handle import DeploymentHandle

from common.embedding_utils import get_model, get_image_embedding, get_text_embedding
from common.types import EmbeddingModel
from common.constants import MAX_CONCURRENCY_PINECONE, NUM_INDICES
from pinecone_utility.query import query_all_indices

fastapi = FastAPI()

logger = logging.getLogger("ray.serve")


def get_max_threads() -> int:
    max_concurrency_global = min(os.cpu_count(), MAX_CONCURRENCY_PINECONE)
    return max_concurrency_global // NUM_INDICES


class SimilarImagesRetriever:
    def __init__(self):
        logger.info("Initializing connection with Pinecone")
        self.pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        logger.info("Connection with Pinecone established...")

        # Instantiate model and processor caches.
        get_model(EmbeddingModel.openai.value)
        get_model(EmbeddingModel.fashionclip.value)

    def rerank_results(self, results: List[Dict[str, Any]]):
        all_modalities_unique = []
        paths_seen = set()
        for image_info in results:
            path = image_info["path"]
            if path not in paths_seen:
                all_modalities_unique.append(image_info)
                paths_seen.add(path)
        sorted_results = sorted(
            all_modalities_unique, key=lambda x: x["score"], reverse=True
        )
        return sorted_results

    def image_search(
        self,
        query_img: Image.Image,
        model: EmbeddingModel,
        num_results: int,
        logger: logging.Logger,
    ):
        logger.info("Computing embeddings for the input query...")
        embeds = get_image_embedding(query_img, model.value)
        logger.info("Embeddings computed successfully!")

        max_threads_to_use = get_max_threads()
        with ThreadPoolExecutor(max_workers=max_threads_to_use) as executor:
            scores = list(
                executor.map(
                    lambda embed: self._retrieve_scores_images(
                        num_results=num_results, embedding=embed, model=model
                    ),
                    embeds,
                )
            )

        return scores

    def text_search(
        self,
        desc: List[str],
        model: EmbeddingModel,
        num_results: int,
        logger: logging.Logger,
    ) -> List[Dict[str, Any]]:
        logger.info("Computing embeddings for the input query...")
        embeds = get_text_embedding(desc, model.value)
        logger.info("Embeddings computed successfully!")

        max_threads_to_use = get_max_threads()
        logger.info("Retrieving images and scores...")
        with ThreadPoolExecutor(max_workers=max_threads_to_use) as executor:
            scores = list(
                executor.map(
                    lambda embed: self._retrieve_scores_images(
                        num_results=num_results, embedding=embed, model=model
                    ),
                    embeds,
                )
            )
        logger.info("Done retrieving images and scores!")
        return scores

    def _retrieve_scores_images(
        self,
        num_results: int,
        embedding: np.ndarray,
        model: EmbeddingModel,
    ) -> List[Dict[str, Any]]:
        matches = query_all_indices(self.pc, model, num_results, embedding)
        reranked_results = self.rerank_results(matches)
        return reranked_results[:num_results]


class TextSearchRequest(BaseModel):
    query: str
    model: EmbeddingModel
    num_results: int = 5


class ImageSearchRequest(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    query: str
    model: EmbeddingModel
    num_results: int = 5


@serve.deployment
@serve.ingress(fastapi)
class MultiModalSimilaritySearchService:
    def __init__(
        self,
        text_search_service: DeploymentHandle,
        img_search_service: DeploymentHandle,
    ):
        self.text_search_service = text_search_service
        self.img_search_service = img_search_service

    @fastapi.post("/ready")
    async def readiness_check(self):
        return {"status": "Ready!"}

    @fastapi.post("/text_search")
    async def return_img_by_text_prompt(self, request: TextSearchRequest):
        result = await self.text_search_service.return_img_by_text_prompt.remote(
            request
        )
        return result

    @fastapi.post("/image_search")
    async def return_img_by_img_prompt(self, request: ImageSearchRequest):
        result = await self.img_search_service.return_img_by_img_prompt.remote(request)
        return result


@serve.deployment(
    num_replicas="auto",
)
class TextSearchService:
    def __init__(self):
        self.retriever = SimilarImagesRetriever()

    @serve.batch(max_batch_size=4, batch_wait_timeout_s=0.1)
    async def return_img_by_text_prompt(
        self, multiple_requests: List
    ) -> List[Dict[str, Any]]:
        logger = logging.getLogger("ray.serve")
        queries = [request.query for request in multiple_requests]
        return self.retriever.text_search(
            desc=queries,
            model=multiple_requests[0].model,
            num_results=multiple_requests[0].num_results,
            logger=logger,
        )


@serve.deployment(
    num_replicas="auto",
)
class ImageSearchService:
    def __init__(self):
        self.retriever = SimilarImagesRetriever()

    @serve.batch(max_batch_size=4, batch_wait_timeout_s=0.1)
    async def return_img_by_img_prompt(
        self, multiple_requests: List
    ) -> List[Dict[str, Any]]:
        logger = logging.getLogger("ray.serve")
        image_arr = [
            Image.fromarray(np.array(json.loads(request.query), dtype=np.uint8))
            for request in multiple_requests
        ]
        return self.retriever.image_search(
            query_img=image_arr,
            model=multiple_requests[0].model,
            num_results=multiple_requests[0].num_results,
            logger=logger,
        )


text_search_service = TextSearchService.bind()
image_search_service = ImageSearchService.bind()
app = MultiModalSimilaritySearchService.bind(text_search_service, image_search_service)
