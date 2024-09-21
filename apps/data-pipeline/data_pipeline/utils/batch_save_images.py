import concurrent.futures

import PIL.Image

from data_pipeline.consts import DAGSTER_STORAGE_BUCKET


def save_image(args):
    img, image_path = args

    # Save the image directly to the Azure Blob
    with image_path.open("wb") as f:
        img.save(f, format="PNG")


def batch_save_images(images, cluster_labels, partition_key, max_workers=100):
    images_folder = DAGSTER_STORAGE_BUCKET / "funny_images" / partition_key
    images_folder.mkdir(parents=True, exist_ok=True)

    # Prepare arguments for each image
    args_list = [
        (img, images_folder / f"{label}.png")
        for img, label in zip(images, cluster_labels)
    ]

    # Use ThreadPoolExecutor for parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and get future objects
        futures = [executor.submit(save_image, args) for args in args_list]

        # Wait for all futures to complete and print results
        for future in concurrent.futures.as_completed(futures):
            future.result()

    return list(map(lambda x: str(x[1]), args_list))


if __name__ == "__main__":
    images = [PIL.Image.new("RGB", (100, 100)) for _ in range(100)]
    cluster_labels = [f"cluster_{i}" for i in range(100)]
    partition_key = "test"
    res = batch_save_images(images, cluster_labels, partition_key)
    print(res)
