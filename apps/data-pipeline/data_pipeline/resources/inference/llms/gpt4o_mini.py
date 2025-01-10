from dagster import EnvVar, build_init_resource_context

from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    LlmConfig,
)
from data_pipeline.resources.inference.llm_factory import create_llm_resource
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig

gpt4o_mini_config_azure = LlmConfig(
    colloquial_model_name="gpt-4o-mini",
    is_multimodal=True,
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_OPENAI_API_KEY"),
        concurrency_limit=50,
        timeout=60 * 10,
        inference_url="https://enclaveidai2163546968.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-08-01-preview",
        inference_config={
            "temperature": 1,
            "max_tokens": 1024,
            "top_p": 1,
            "model": "gpt-4o-mini",
            "frequency_penalty": 0,
            "presence_penalty": 0,
        },
        input_cpm=0.15 / 1000,
        output_cpm=0.6 / 1000,
        context_length=128_000,
    ),
)


gpt4o_mini_config_openrouter = LlmConfig(
    colloquial_model_name="gpt-4o-mini",
    is_multimodal=True,
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("OPENROUTER_API_KEY"),
        concurrency_limit=200,
        timeout=60 * 10,
        inference_url="https://openrouter.ai/api/v1/chat/completions",
        inference_config={
            "temperature": 1,
            "max_tokens": 1024,
            "top_p": 1,
            "model": "openai/gpt-4o-mini",
            "frequency_penalty": 0,
            "presence_penalty": 0,
        },
        input_cpm=0.15 / 1000,
        output_cpm=0.6 / 1000,
        context_length=128_000,
    ),
)


# TODO: Switch to Azure in production
def create_gpt4o_mini_resource() -> BaseLlmResource:
    return create_llm_resource(gpt4o_mini_config_azure)


if __name__ == "__main__":
    import os
    import time

    import dotenv

    dotenv.load_dotenv()

    # Need to manaully read the api key from the env
    test_config = gpt4o_mini_config_azure.model_copy(
        update={
            "remote_llm_config": gpt4o_mini_config_azure.remote_llm_config.model_copy(
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
