from dagster import EnvVar, build_init_resource_context

from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.resources.inference.llm_factory import LlmConfig, create_llm_resource
from data_pipeline.resources.inference.remote_llm_config import RemoteLlmConfig

# TODO: Implement batch https://platform.openai.com/docs/api-reference/batch
gpt4o_config = LlmConfig(
    colloquial_model_name="gpt-4o",
    is_multimodal=True,
    remote_llm_config=RemoteLlmConfig(
        api_key=EnvVar("AZURE_AI_GPT4O_API_KEY"),
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
        input_cpm=2.75 / 1000,
        output_cpm=11 / 1000,
        context_length=128_000,
    ),
)


def create_gpt4o_resource() -> BaseLlmResource:
    return create_llm_resource(gpt4o_config)


if __name__ == "__main__":
    resource = create_gpt4o_resource()
    resource.setup_for_execution(build_init_resource_context())
    print(resource.get_prompt_sequences_completions_batch([["Hello, how are you?"]]))
