import json
import time

from data_pipeline.utils.capabilities import gpu_info

A100_HOURLY_COST = 3.67


def get_gpu_runtime_cost(start_time: float) -> float:
    runtime_s = time.time() - start_time
    try:
        return runtime_s / 3600 * A100_HOURLY_COST * len(json.loads(gpu_info()))
    except Exception:
        return 0.0
