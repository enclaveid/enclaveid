import time

GPU_HOURLY_COST = 3.67


def get_gpu_runtime_cost(start_time: float) -> float:
    runtime_s = time.time() - start_time
    return runtime_s / 3600 * GPU_HOURLY_COST
