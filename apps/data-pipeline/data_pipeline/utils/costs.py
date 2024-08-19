import time

NC48ads_A100_v4_HOURLY_COST_SPOT = 0.8889


def get_gpu_runtime_cost(start_time: float) -> float:
    runtime_s = time.time() - start_time
    try:
        return runtime_s / 3600 * NC48ads_A100_v4_HOURLY_COST_SPOT
    except Exception:
        return 0.0
