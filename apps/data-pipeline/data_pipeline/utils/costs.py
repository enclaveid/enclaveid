import time

NC24ads_A100_v4_HOURLY_COST_SPOT = 0.44445


def get_gpu_runtime_cost(start_time: float, gpu_count: int = 1) -> float:
    runtime_s = time.time() - start_time
    try:
        return runtime_s / 3600 * NC24ads_A100_v4_HOURLY_COST_SPOT * gpu_count
    except Exception:
        return 0.0
