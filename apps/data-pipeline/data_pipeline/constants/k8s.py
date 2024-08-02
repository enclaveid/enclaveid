from data_pipeline.utils.deep_merge import deep_merge

base_k8s_gpu_config = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {
                    "nvidia.com/gpu": "1",
                },
                "limits": {
                    "nvidia.com/gpu": "1",
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
    base_k8s_gpu_config,
    {
        "dagster-k8s/config": {
            "container_config": {
                "image": "enclaveid/data-pipeline-vllm:master",
                "volumeMounts": [{"name": "model-cache", "mountPath": "/model-cache"}],
                # TODO: Figure out a better set of permissions for podman-built
                # # images to access the model cache
                "securityContext": {
                    "allowPrivilegeEscalation": False,
                    "runAsUser": 0,
                },
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
    base_k8s_gpu_config,
    {
        "dagster-k8s/config": {
            "container_config": {
                "image": "enclaveid/data-pipeline-rapids:master",
            }
        }
    },
)
