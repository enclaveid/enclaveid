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
                    }
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
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
            },
        }
    }


k8s_vllm_config = deep_merge(
    get_base_k8s_gpu_config(2),
    {
        "dagster-k8s/config": {
            "container_config": {
                "image": "enclaveid/data-pipeline-vllm:master",
                "volumeMounts": [{"name": "model-cache", "mountPath": "/model-cache"}],
            },
            "pod_spec_config": {
                "volumes": [
                    {
                        "name": "model-cache",
                        "persistentVolumeClaim": {
                            "claimName": "enclaveid-model-cache-pvc"
                        },
                    }
                ],
            },
        }
    },
)

k8s_rapids_config = deep_merge(
    get_base_k8s_gpu_config(1),
    {
        "dagster-k8s/config": {
            "container_config": {
                "image": "enclaveid/data-pipeline-rapids:master",
            }
        }
    },
)
