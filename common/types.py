from enum import Enum


class EmbeddingModel(str, Enum):
    openai = "openai/clip-vit-base-patch32"
    fashionclip = "patrickjohncyh/fashion-clip"


class EmbeddingType(str, Enum):
    img = "Image"
    txt = "Text"
