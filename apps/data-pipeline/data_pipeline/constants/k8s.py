import os

from data_pipeline.utils.data_structures import deep_merge


def get_base_k8s_gpu_config(gpu_count):
    return {
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {
                        "nvidia.com/gpu": str(gpu_count),
                    },
                    "limits": {
                        "nvidia.com/gpu": str(gpu_count),
                    },
                },
            },
            "pod_spec_config": {
                "tolerations": [
                    {
                        "key": "sku",
                        "operator": "Equal",
                        "value": "gpu",
                        "effect": "NoSchedule",
                    },
                    {
                        "key": "kubernetes.azure.com/scalesetpriority",
                        "operator": "Equal",
                        "value": "spot",
                        "effect": "NoSchedule",
                    },
                ],
                "affinity": {
                    "node_affinity": {
                        "required_during_scheduling_ignored_during_execution": {
                            "node_selector_terms": [
                                {
                                    "match_expressions": [
                                        {
                                            "key": "sku",
                                            "operator": "In",
                                            "values": ["gpu"],
                                        },
                                        {
                                            "key": "kubernetes.azure.com/scalesetpriority",
                                            "operator": "In",
                                            "values": ["spot"],
                                        },
                                        {
                                            "key": "gpu-count",
                                            "operator": "In",
                                            "values": [str(gpu_count)],
                                        },
                                    ]
                                }
                            ]
                        }
                    }
                },
            },
        }
    }


def get_k8s_vllm_config(gpu_count=4, shm_size_gb=250):
    return deep_merge(
        get_base_k8s_gpu_config(gpu_count),
        {
            "dagster-k8s/config": {
                "container_config": {
                    "image": os.environ.get("VLLM_IMAGE", ""),
                    "volumeMounts": [{"name": "dshm", "mountPath": "/dev/shm"}],
                },
                "pod_spec_config": {
                    "volumes": [
                        {
                            "name": "dshm",
                            "empty_dir": {
                                "medium": "Memory",
                                "size_limit": f"{shm_size_gb}Gi",
                            },
                        }
                    ],
                },
            }
        },
    )


# TODO: We'll be requesting the 4 gpu instance for now even if the code only uses 1.
# The clustering is already really quick so we'd rather not wait for the nodes to scale down and up.
def get_k8s_rapids_config(gpu_count=4):
    return deep_merge(
        get_base_k8s_gpu_config(gpu_count),
        {
            "dagster-k8s/config": {
                "container_config": {
                    "image": os.environ.get("RAPIDS_IMAGE", ""),
                }
            }
        },
    )
