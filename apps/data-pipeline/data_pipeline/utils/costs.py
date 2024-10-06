import time

from data_pipeline.utils.capabilities import gpu_info

NC24ads_A100_v4_HOURLY_COST_SPOT = 0.5


def get_gpu_runtime_cost(start_time: float) -> float:
    gpu_count = len(gpu_info(return_list=True))
    runtime_s = time.time() - start_time
    try:
        return runtime_s / 3600 * NC24ads_A100_v4_HOURLY_COST_SPOT * gpu_count
    except Exception:
        return 0.0
