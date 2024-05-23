import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPTokenizer


class ProcessImagesCLIP:
    def __init__(self, model_id: str) -> None:
        self.processor = CLIPProcessor.from_pretrained(model_id)

    def __call__(self, row: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        row["pixel_values"] = self.processor(
            text=None,
            images=Image.fromarray(row["image"]),
            return_tensors="pt",
        )["pixel_values"][0]
        return row


class ProcessTextCLIP:
    def __init__(self, model_id: str) -> None:
        self.tokenizer = CLIPTokenizer.from_pretrained(model_id)

    def __call__(self, row: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        tokenized = self.tokenizer(
            row["new_desc"],
            return_tensors="pt",
            padding="max_length",
            max_length=None,
            truncation=True,
        )
        row["input_ids"] = tokenized["input_ids"][0]
        row["attention_mask"] = tokenized["attention_mask"][0]
        return row
