from typing import TYPE_CHECKING, List

import ray
from dagster import ConfigurableResource, InitResourceContext

from data_pipeline.utils.capabilities import is_vllm_image
from data_pipeline.utils.data_structures import flatten

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

    def generate(self, prompts: List[str]):
        chunk_size = 200
        results = []

        for i in range(0, len(prompts), chunk_size):
            results.append(
                self.pipe(
                    prompt=prompts[i : i + chunk_size],
                    guidance_scale=3.5,
                    height=640,
                    width=360,
                    num_inference_steps=50,
                    max_sequence_length=256,
                ).images
            )

        return flatten(results)


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

    def generate_images(self, prompts: List[str]):
        # Distribute prompts evenly across the GPUs while preserving order
        chunks = [
            prompts[i : i + len(prompts) // len(self._generators)]
            for i in range(0, len(prompts), len(prompts) // len(self._generators))
        ]

        # Use Ray to run the generators in parallel
        refs = [
            generator.generate.remote(chunk)
            for generator, chunk in zip(self._generators, chunks)
        ]
        results = ray.get(refs)

        # Flatten the results and ensure they're in the original order
        return [image for batch in zip(*results) for image in batch]

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        context.log.info("Shutting down Ray")
        ray.shutdown()
