from typing import List, Union

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor, CLIPTokenizer


def get_model(model_id: str) -> tuple[CLIPModel, CLIPProcessor, CLIPTokenizer]:
    tokenizer = CLIPTokenizer.from_pretrained(model_id)
    model = CLIPModel.from_pretrained(model_id).to(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    processor = CLIPProcessor.from_pretrained(model_id)
    return model, processor, tokenizer


def get_text_embedding(text: Union[str, List[str]], model_id: str) -> np.ndarray:
    model, processor, tokenizer = get_model(model_id)
    tokenized_text = tokenizer(text, return_tensors="pt").to(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    return model.get_text_features(**tokenized_text).cpu().detach().numpy()


def get_image_embedding(
    image: Union[Image.Image, List[Image.Image]], model_id: str
) -> np.ndarray:
    model, processor, tokenizer = get_model(model_id)
    img = processor(
        text=None,
        images=image,
        return_tensors="pt",
    )[
        "pixel_values"
    ].to("cuda" if torch.cuda.is_available() else "cpu")
    return model.get_image_features(img).detach().cpu().numpy()
