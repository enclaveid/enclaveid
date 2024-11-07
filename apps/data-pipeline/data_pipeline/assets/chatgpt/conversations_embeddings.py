import os

from dagster import AssetExecutionContext, asset
from dagster_ray.kuberay.pipes import PipesKubeRayJobClient

import data_pipeline.ray_jobs.distributed_embeddings as distributed_embeddings_job
from data_pipeline.assets.chatgpt.conversation_summaries import conversation_summaries
from data_pipeline.partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    deps=[conversation_summaries],
    # io_manager_key="parquet_io_manager",
    # ins={
    #     "conversation_summaries": AssetIn(
    #         key=["conversation_summaries"],
    #     ),
    # },
    # op_tags=get_k8s_vllm_config(gpu_count=1),
)
def conversations_embeddings(
    context: AssetExecutionContext,
    pipes_kube_rayjob_client: PipesKubeRayJobClient,
):
    pipes_kube_rayjob_client.run(
        context=context,
        ray_job={
            "apiVersion": "ray.io/v1",
            "kind": "RayJob",
            "metadata": {
                "name": "conversations-embeddings",
                "namespace": "ray",
            },
            "spec": {
                "entrypoint": f"python -m {distributed_embeddings_job.__name__}",
                "rayClusterSpec": {
                    "headGroupSpec": {
                        "rayStartParams": {
                            "dashboard-host": "0.0.0.0",
                            "block": "true",
                        },
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "ray-head",
                                        "image": os.environ.get("BASE_IMAGE", ""),
                                    }
                                ]
                            }
                        },
                    },
                    "workerGroupSpecs": [
                        {
                            "groupName": "gpu-workers",
                            "rayStartParams": {"block": "true"},
                            "replicas": 4,
                            "template": {
                                "spec": {
                                    "containers": [
                                        {
                                            "name": "ray-worker",
                                            "image": os.environ.get("VLLM_IMAGE", ""),
                                            "resources": {
                                                "requests": {"nvidia.com/gpu": "1"},
                                                "limits": {"nvidia.com/gpu": "1"},
                                            },
                                            "volumeMounts": [
                                                {
                                                    "name": "dshm",
                                                    "mountPath": "/dev/shm",
                                                }
                                            ],
                                        }
                                    ],
                                    "volumes": [
                                        {
                                            "name": "dshm",
                                            "emptyDir": {
                                                "medium": "Memory",
                                                "sizeLimit": "64Gi",
                                            },
                                        }
                                    ],
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
                                        "nodeAffinity": {
                                            "requiredDuringSchedulingIgnoredDuringExecution": {
                                                "nodeSelectorTerms": [
                                                    {
                                                        "matchExpressions": [
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
                                                                "values": ["1"],
                                                            },
                                                        ]
                                                    }
                                                ]
                                            }
                                        }
                                    },
                                }
                            },
                        }
                    ],
                },
            },
        },
    )
