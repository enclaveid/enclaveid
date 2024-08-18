import time

import torch

A100_HOURLY_COST = 3.67


def get_gpu_runtime_cost(start_time: float) -> float:
    num_gpus = torch.cuda.device_count()
    runtime_s = time.time() - start_time
    return runtime_s / 3600 * A100_HOURLY_COST * num_gpus
