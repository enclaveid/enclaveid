import json
from dataclasses import asdict

from huggingface_hub import scan_cache_dir


def get_hf_cache_info() -> str:
    cache_info = scan_cache_dir()

    # Convert the object to a dictionary
    cache_dict = asdict(cache_info)

    # Convert PosixPath objects to strings
    for repo in cache_dict["repos"]:
        repo["repo_path"] = str(repo["repo_path"])

    # Convert warnings to a list of dictionaries
    cache_dict["warnings"] = [
        {"type": "CorruptedCacheException", "message": str(w.args[0])}
        for w in cache_info.warnings
    ]

    # Convert to JSON string
    return json.dumps(cache_dict, indent=2)
