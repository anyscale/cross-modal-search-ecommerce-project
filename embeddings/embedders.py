import numpy as np
import torch
from transformers import CLIPModel


class EmbedImagesCLIP:
    def __init__(self, model_id: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained(model_id).to(self.device)

    def __call__(self, batch: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        batch["image_embeddings"] = (
            self.model.get_image_features(
                torch.tensor(data=batch["pixel_values"], device=self.device)
            )
            .detach()
            .cpu()
            .numpy()
        )
        return batch


class EmbedTextCLIP:
    def __init__(self, model_id: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained(model_id).to(self.device)

    def __call__(self, batch: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        text_embeddings = (
            self.model.get_text_features(
                input_ids=torch.tensor(data=batch["input_ids"], device=self.device),
                attention_mask=torch.tensor(
                    data=batch["attention_mask"], device=self.device
                ),
            )
            .detach()
            .cpu()
            .numpy()
        )
        batch["text_embeddings"] = text_embeddings
        return batch
