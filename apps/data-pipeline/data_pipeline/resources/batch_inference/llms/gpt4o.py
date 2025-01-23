from dagster import EnvVar, build_init_resource_context

from data_pipeline.resources.batch_inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.batch_inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.batch_inference.remote_llm_config import RemoteLlmConfig

# TODO: Implement batch https://platform.openai.com/docs/api-reference/batch
gpt4o_config = LlmConfig(
    colloquial_model_name="gpt-4o",
    is_multimodal=True,
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_OPENAI_API_KEY"),
        concurrency_limit=32,
        timeout=60 * 10,
        inference_url="https://enclaveidai2163546968.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview",
        inference_config={
            "temperature": 1,
            "max_tokens": 1024,
            "top_p": 1,
            "model": "gpt-4o",
            "frequency_penalty": 0,
            "presence_penalty": 0,
        },
        input_cpm=2.5 / 1000,
        output_cpm=10 / 1000,
        context_length=128_000,
    ),
)


def create_gpt4o_resource() -> BaseLlmResource:
    return create_llm_resource(gpt4o_config)


if __name__ == "__main__":
    import os
    import time

    import dotenv

    dotenv.load_dotenv()

    # Need to manaully read the api key from the env
    test_config = gpt4o_config.model_copy(
        update={
            "remote_llm_config": gpt4o_config.remote_llm_config.model_copy(
                update={"api_key": os.environ["AZURE_OPENAI_API_KEY"]}
            )
        }
    )
    resource = create_llm_resource(test_config)
    context = build_init_resource_context()
    resource.setup_for_execution(context)
    t0 = time.time()
    print(resource.get_prompt_sequences_completions_batch([["Hi"]]))
    print(time.time() - t0)
