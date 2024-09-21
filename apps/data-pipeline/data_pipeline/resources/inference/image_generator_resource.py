from typing import TYPE_CHECKING, Dict, List

import PIL.Image
import ray
from dagster import ConfigurableResource, InitResourceContext

from data_pipeline.utils.capabilities import is_vllm_image

if is_vllm_image() or TYPE_CHECKING:
    import torch
    from diffusers import FluxPipeline
else:
    torch = None
    FluxPipeline = None


@ray.remote(num_gpus=1)
class RayImageGenerator:
    def __init__(self, model_name: str):
        self.pipe = FluxPipeline.from_pretrained(model_name, torch_dtype=torch.bfloat16)
        self.pipe.vae.enable_slicing()
        self.pipe.vae.enable_tiling()
        self.pipe.to("cuda")

    def generate(self, prompts: List[str], cluster_labels: List[int]):
        chunk_size = 200
        results = []

        for i in range(0, len(prompts), chunk_size):
            results.extend(
                self.pipe(
                    prompt=prompts[i : i + chunk_size],
                    guidance_scale=3.5,
                    height=640,
                    width=360,
                    num_inference_steps=50,
                    max_sequence_length=256,
                ).images
            )

        return results, cluster_labels


class ImageGeneratorResource(ConfigurableResource):
    _model_name = "black-forest-labs/FLUX.1-dev"
    _generators: List[ray.ObjectRef] = []

    def setup_for_execution(self, context: InitResourceContext) -> None:
        ray.init()
        self._generators = [
            RayImageGenerator.remote(self._model_name)
            for _ in range(torch.cuda.device_count())
        ]
        context.log.info(f"Initialized {len(self._generators)} image generators")

    def generate_images(
        self, prompts: List[str], cluster_labels
    ) -> Dict[int, PIL.Image.Image]:
        # Distribute prompts and cluster_labels evenly across the GPUs
        chunks = [[] for _ in self._generators]
        label_chunks = [[] for _ in self._generators]
        for i, (prompt, label) in enumerate(zip(prompts, cluster_labels)):
            generator_index = i % len(self._generators)
            chunks[generator_index].append(prompt)
            label_chunks[generator_index].append(label)

        # Use Ray to run the generators in parallel
        refs = [
            generator.generate.remote(chunk, label_chunk)
            for generator, chunk, label_chunk in zip(
                self._generators, chunks, label_chunks
            )
        ]
        results = ray.get(refs)

        result_dict = {}
        for images, labels in results:
            for image, label in zip(images, labels):
                if label not in result_dict:
                    result_dict[label] = image

        return result_dict

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        context.log.info("Shutting down Ray")
        ray.shutdown()
