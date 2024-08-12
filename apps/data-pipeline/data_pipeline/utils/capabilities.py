import importlib.util
import subprocess

MIN_CUDA_COMPUTE_CAPABILITY = 7.0


def gpu_info():
    try:
        return subprocess.run(
            "nvidia-smi --query-gpu=timestamp,name,pci.bus_id,driver_version,pstate,pcie.link.gen.max,pcie.link.gen.current,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv,noheader",
            shell=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
    except Exception:
        return "No GPU information available."


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
