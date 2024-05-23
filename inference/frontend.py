import json
from typing import Dict, List, Tuple

import gradio as gr
import numpy as np
import requests
from PIL import Image
from ray.serve.gradio_integrations import GradioServer

from common.constants import ANYSCALE_BACKEND_SERVICE_URL, DATASET_URL


def prepare_output(results: List[Dict]) -> List[Tuple[str, str]]:
    results_img_score_list = []

    # Iterate over the results_list
    for result in results:
        path = result["path"]
        score = result["score"]
        image_path = f"{DATASET_URL}{path}"
        results_img_score_list.append((image_path, f"Score: {score:.2f}"))
    return results_img_score_list


def gradio_summarizer_builder() -> gr.TabbedInterface:
    # Define callback function (search by text)
    def request_text_search(
        text_query: str, embedding_model: str, num_results: str
    ) -> List[Tuple[str, str]]:
        response = requests.post(
            f"{ANYSCALE_BACKEND_SERVICE_URL}/text_search",
            json={
                "query": text_query,
                "model": embedding_model,
                "num_results": num_results,
            },
        )
        results = response.json()
        return prepare_output(results)

    # Define callback function (search by image)
    def request_image_search(
        image_query: Image.Image, embedding_model: str, num_results: str
    ) -> List[Tuple[str, str]]:
        image_dump = json.dumps(np.array(image_query).tolist())

        response = requests.post(
            f"{ANYSCALE_BACKEND_SERVICE_URL}/image_search",
            json={
                "query": image_dump,
                "model": embedding_model,
                "num_results": num_results,
            },
        )
        results = response.json()

        return prepare_output(results)

    # Text interface
    text_search_interface = gr.Interface(
        fn=request_text_search,
        inputs=[
            gr.Textbox(value="a man in a blue shirt", label="Query"),
            gr.Dropdown(
                ["patrickjohncyh/fashion-clip", "openai/clip-vit-base-patch32"],
                label="Embedding model",
                info="Which model to use?",
                value="patrickjohncyh/fashion-clip",
            ),
            gr.Slider(
                3, 9, value=3, step=3, label="Results", info="How many results to show?"
            ),
        ],
        outputs=gr.Gallery(
            label="Generated images",
            show_label=False,
            elem_id="gallery",
            columns=[3],
            object_fit="contain",
            height="auto",
        ),
        allow_flagging="never",
    )

    # Image interface
    image_search_interface = gr.Interface(
        request_image_search,
        inputs=[
            gr.Image(),
            gr.Dropdown(
                ["patrickjohncyh/fashion-clip", "openai/clip-vit-base-patch32"],
                label="Embedding model",
                info="Which model to use?",
                value="patrickjohncyh/fashion-clip",
            ),
            gr.Slider(
                3, 9, value=3, step=3, label="Results", info="How many results to show?"
            ),
        ],
        outputs=gr.Gallery(
            label="Generated images",
            show_label=False,
            elem_id="gallery",
            columns=[3],
            object_fit="contain",
            height="auto",
        ),
        allow_flagging="never",
    )

    # Composition (tabs)
    return gr.TabbedInterface(
        [text_search_interface, image_search_interface],
        ["Search by text", "Search by image"],
        title="Multi-modal Similarity Search",
        theme="sudeepshouche/minimalist",
    )


app = GradioServer.options(ray_actor_options={"num_cpus": 1}).bind(
    gradio_summarizer_builder
)
