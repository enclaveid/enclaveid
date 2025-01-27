import os
import time

import dotenv
from dagster import build_init_resource_context

from data_pipeline.resources.batch_inference.base_llm_resource import LlmConfig
from data_pipeline.resources.batch_inference.llm_factory import create_llm_resource


def test_remote_llm_call(config: LlmConfig, api_key_var_name: str):
    dotenv.load_dotenv()

    # Need to manaully read the api key from the env
    test_config = config.model_copy(
        update={
            "remote_llm_config": config.remote_llm_config.model_copy(  # type: ignore
                update={"api_key": os.environ[api_key_var_name]}
            )
        }
    )
    resource = create_llm_resource(test_config)
    context = build_init_resource_context()
    resource.setup_for_execution(context)  # type: ignore
    t0 = time.time()
    print(resource.get_prompt_sequences_completions_batch([["Hi"]]))  # type: ignore
    print(time.time() - t0)
