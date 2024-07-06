import asyncio
from typing import Dict, List

import httpx


async def _get_completion(
    async_client: httpx.AsyncClient, conversation: List[Dict[str, str]], api_key: str
) -> str:
    payload = {
        "messages": conversation,
        "max_tokens": 128,
        "temperature": 0.8,
        "top_p": 0.1,
        "best_of": 1,
        "presence_penalty": 0,
        "use_beam_search": "false",
        "ignore_eos": "false",
        "skip_special_tokens": "false",
        "logprobs": "false",
    }
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    response = await async_client.post(
        "https://Meta-Llama-3-70B-Instruct-pbssd-serverless.eastus2.inference.ai.azure.com/v1/chat/completions",
        json=payload,
        headers=headers,
    )
    response.raise_for_status()
    res = response.json()
    return res["choices"][0]["message"]["content"]


async def _get_prompt_sequence_completion(
    async_client: httpx.AsyncClient, prompts_sequence: List[str], api_key: str
):
    conversation: List[Dict[str, str]] = []
    response = ""

    for prompt in prompts_sequence:
        conversation.append({"role": "user", "content": prompt})
        response = await _get_completion(async_client, conversation, api_key)
        conversation.append({"role": "assistant", "content": response})
    return {"conversation": conversation, "final_answer": response}


async def get_llama70b_completions(prompts: List[List[str]], api_key: str):
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=256, max_keepalive_connections=256),
        timeout=60 * 10,
    ) as client:
        return await asyncio.gather(
            *(
                _get_prompt_sequence_completion(client, prompt_list, api_key)
                for prompt_list in prompts
            )
        )
