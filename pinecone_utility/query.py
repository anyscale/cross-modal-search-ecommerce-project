from typing import Any, Dict, List

import threading
import pinecone
import numpy as np

from common.types import EmbeddingModel
from pinecone_utility.utils import get_index_name


def process_query_output(pc_query_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    matches = pc_query_output["matches"]
    img_paths = [match["id"] for match in matches]
    scores = [match["score"] for match in matches]
    results = [{"path": path, "score": score} for path, score in zip(img_paths, scores)]
    return results


def query(
    pc: pinecone.Pinecone, index_name: str, num_results: int, vector: List[float]
) -> List[Dict[str, Any]]:
    query_output = pc.Index(index_name).query(
        namespace="ns1",
        vector=vector,
        top_k=num_results,
        include_values=True,
        include_metadata=True,
    )
    return process_query_output(query_output)


def query_all_indices(
    pc: pinecone.Pinecone,
    model: EmbeddingModel,
    num_results: int,
    embedding: np.ndarray,
) -> List[Dict[str, Any]]:

    def query_index_async(index_name, num_results, vector, results_list):
        results = query(pc, index_name, num_results, vector)
        results_list.extend(results)

    results_img_index = []
    results_txt_index = []

    img_thread = threading.Thread(
        target=query_index_async,
        args=(
            get_index_name(model_name=model.name, modality="img"),
            num_results,
            embedding.tolist(),
            results_img_index,
        ),
    )
    txt_thread = threading.Thread(
        target=query_index_async,
        args=(
            get_index_name(model_name=model.name, modality="txt"),
            num_results,
            embedding.tolist(),
            results_txt_index,
        ),
    )

    img_thread.start()
    txt_thread.start()

    img_thread.join()
    txt_thread.join()

    results_all_modalities = results_img_index + results_txt_index
    return results_all_modalities
