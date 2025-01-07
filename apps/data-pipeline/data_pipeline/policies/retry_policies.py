from dagster import Backoff, Jitter, RetryPolicy

spot_instance_retry_policy = RetryPolicy(
    max_retries=3,
    delay=30,
    backoff=Backoff.EXPONENTIAL,
    jitter=Jitter.FULL,
)
