import os

import ray
import typer
from pyarrow import csv

from common.constants import ANN_CSV_URL, DATASET_DIR, DATASET_PATH
from common.types import EmbeddingModel
from embeddings.embedders import EmbedImagesCLIP, EmbedTextCLIP
from pinecone_utility.setup import setup_pinecone
from pinecone_utility.utils import (
    get_index_name,
    convert_text_emb_to_pc_vector,
    convert_image_emb_to_pc_vector
)
from pinecone_utility.upsert import UpsertVectors
from embeddings.processors import ProcessImagesCLIP, ProcessTextCLIP

app = typer.Typer()


def process_image_embeddings(
    dataset_url: str,
    ann_csv_url: str,
    index_name: str,
    namespace: str,
    model_id: str,
    embedding_batch_size: int = 100,
    vector_upsert_batch_size: int = 100,
    img_processing_concurrency: int = 2,
    embedding_concurrency: int = 2,
    vector_upsert_concurrency: int = 9,
) -> None:
    images_ray_dataset = ray.data.read_images(
        dataset_url, include_paths=True, size=(512, 512)
    )
    parse_options = csv.ParseOptions(delimiter="#", newlines_in_values=True)
    txt_ray_dataset = ray.data.read_csv(ann_csv_url, parse_options=parse_options)
    image_paths = txt_ray_dataset.unique("image_path")
    filtered_img_dataset = images_ray_dataset.filter(
        lambda row: os.path.join(
            os.path.basename(row["path"]),
        )
        in image_paths
    )
    processed_images = filtered_img_dataset.map(
        ProcessImagesCLIP,
        num_cpus=1,
        fn_constructor_kwargs={"model_id": model_id},
        concurrency=img_processing_concurrency,
    )
    embedded_images = processed_images.map_batches(
        EmbedImagesCLIP,
        batch_size=embedding_batch_size,
        num_gpus=1,
        fn_constructor_kwargs={"model_id": model_id},
        concurrency=embedding_concurrency,
    )
    pinecone_ds = embedded_images.map(convert_image_emb_to_pc_vector)
    upserted_vector = pinecone_ds.map_batches(
        UpsertVectors,
        concurrency=vector_upsert_concurrency,
        batch_size=vector_upsert_batch_size,
        num_cpus=1,
        fn_constructor_args=[index_name, namespace],
    )
    upserted_vector.materialize()


def process_text_embeddings(
    dataset_url: str,
    ann_csv_url: str,
    index_name: str,
    namespace: str,
    model_id: str,
    txt_embedd_batch_size: int = 100,
    txt_embedd_concurrency: int = 2,
    txt_tokenize_concurrency: int = 10,
    vector_upsert_batch_size: int = 100,
    vector_upsert_concurrency: int = 9,
) -> None:
    parse_options = csv.ParseOptions(delimiter="#", newlines_in_values=True)
    txt_ray_dataset = ray.data.read_csv(ann_csv_url, parse_options=parse_options)
    img_dataset = ray.data.read_images(dataset_url, include_paths=True)
    image_paths = img_dataset.unique("path")
    filtered_csv_dataset = txt_ray_dataset.filter(
        lambda row: os.path.join(
            DATASET_DIR,
            row["image_path"],
        )
        in image_paths
    )
    tokenized_batches = filtered_csv_dataset.map(
        ProcessTextCLIP,
        num_cpus=1,
        fn_constructor_kwargs={"model_id": model_id},
        concurrency=txt_tokenize_concurrency,
    )
    embedded_descr = tokenized_batches.map_batches(
        EmbedTextCLIP,
        batch_size=txt_embedd_batch_size,
        num_gpus=1,
        fn_constructor_kwargs={"model_id": model_id},
        concurrency=txt_embedd_concurrency,
    )
    pinecone_ds = embedded_descr.map(convert_text_emb_to_pc_vector)
    upserted_vector = pinecone_ds.map_batches(
        UpsertVectors,
        concurrency=vector_upsert_concurrency,
        batch_size=vector_upsert_batch_size,
        num_cpus=1,
        fn_constructor_args=[index_name, namespace],
    )

    upserted_vector.materialize()


@app.command()
def calculate_embeddings_ray(
    mode: str = typer.Option(
        "img", help="Choose mode from: 'txt' or 'img'", case_sensitive=True
    ),
    vector_dim: int = 512,
    ann_csv_url: str = ANN_CSV_URL,
    images_dir_path: str = DATASET_PATH,
    model_name: str = typer.Option(
        "fashionclip",
        help="Choose model from: 'fashionclip' or 'openai'",
        case_sensitive=True,
    ),
    namespace: str = "ns1",
    img_embedd_batch_size: int = 100,
    img_processing_concurrency: int = 2,
    img_embedd_concurrency: int = 2,
    txt_embedd_batch_size: int = 100,
    txt_embedd_concurrency: int = 2,
    txt_tokenize_concurrency: int = 10,
    vector_upsert_batch_size: int = 100,
    vector_upsert_concurrency: int = 9,
) -> None:
    model_id = EmbeddingModel[model_name].value
    index_name = get_index_name(model_name=model_name, modality=mode)
    ray.get(setup_pinecone.remote(index_name, vector_dim))
    if mode == "img":
        process_image_embeddings(
            images_dir_path,
            ann_csv_url,
            index_name,
            namespace,
            model_id,
            img_embedd_batch_size,
            vector_upsert_batch_size,
            img_processing_concurrency,
            img_embedd_concurrency,
            vector_upsert_concurrency,
        )

    elif mode == "txt":
        process_text_embeddings(
            images_dir_path,
            ann_csv_url,
            index_name,
            namespace,
            model_id,
            txt_embedd_batch_size,
            txt_embedd_concurrency,
            txt_tokenize_concurrency,
            vector_upsert_batch_size,
            vector_upsert_concurrency,
        )


if __name__ == "__main__":
    app()
