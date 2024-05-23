import os

def get_index_name(model_name: str, modality: str) -> str:
    return f"{model_name}-{modality}"


def convert_image_emb_to_pc_vector(row: dict) -> dict:
    return {
        "id": os.path.basename(row["path"]),
        "values": row["image_embeddings"],
    }


def convert_text_emb_to_pc_vector(row: dict) -> dict:
    return {
        "id": os.path.basename(row["image_path"]),
        "values": row["text_embeddings"],
    }
