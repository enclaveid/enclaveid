k8s_gpu_config = {
    "dagster-k8s/config": {
        "container_config": {
            "image": "enclaveid/data-pipeline-ml:master",
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
