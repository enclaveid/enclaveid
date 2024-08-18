import jsonpickle
from huggingface_hub import scan_cache_dir


def get_hf_cache_info():
    cache_info = scan_cache_dir()

    # Configure jsonpickle to produce human-readable output
    jsonpickle.set_encoder_options("json", indent=2, sort_keys=True)

    # Use jsonpickle to serialize the entire cache_info object
    serialized_cache_info = jsonpickle.encode(cache_info)

    return serialized_cache_info
