import csv
import importlib.util
import json
import subprocess

import jsonpickle
from huggingface_hub import scan_cache_dir


def nvsmi_csv_to_json(csv_string):
    # Split the CSV string into lines
    csv_lines = csv_string.strip().split("\n")
    # Read the CSV data
    reader = csv.DictReader(csv_lines)
    # Convert the CSV data to a list of dictionaries, cleaning keys and values
    data = [
        {k.strip().replace(" ", "_").lower(): v.strip() for k, v in row.items()}
        for row in reader
    ]
    # Convert to JSON
    return data


MIN_CUDA_COMPUTE_CAPABILITY = 7.0


def gpu_info(return_list=False):
    try:
        csv_string = subprocess.run(
            "nvidia-smi --query-gpu=timestamp,name,pci.bus_id,driver_version,pstate,pcie.link.gen.max,pcie.link.gen.current,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv",
            shell=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        data = nvsmi_csv_to_json(csv_string)

        if return_list:
            return data
        else:
            return json.dumps(data, indent=2)
    except Exception:
        return []


def is_package_installed(package_name):
    spec = importlib.util.find_spec(package_name)
    return spec is not None


def get_cuda_version():
    try:
        cuda_version = subprocess.run(
            "nvcc --version",
            shell=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        return cuda_version
    except Exception:
        return None


def is_cuda_available():
    try:
        compute_capability = subprocess.run(
            "nvidia-smi --query-gpu=compute_cap --format=csv,noheader|head -n 1",
            shell=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        return float(compute_capability) >= MIN_CUDA_COMPUTE_CAPABILITY
    except Exception:
        return False


def is_vllm_image():
    return is_package_installed("torch") and is_cuda_available()


def is_rapids_image():
    return is_package_installed("cudf") and is_cuda_available()


def get_hf_cache_info():
    cache_info = scan_cache_dir()

    # Configure jsonpickle to produce human-readable output
    jsonpickle.set_encoder_options("json", indent=2, sort_keys=True)

    # Use jsonpickle to serialize the entire cache_info object
    serialized_cache_info = jsonpickle.encode(cache_info)

    return serialized_cache_info
