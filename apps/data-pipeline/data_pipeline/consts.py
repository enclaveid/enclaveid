import os

from upath import UPath


def get_environment() -> str:
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "prod":
        return "PROD"
    return "LOCAL"


DEPLOYMENT_TYPE = get_environment()

# TODO: why do we need so many different buckets? confusing
PRODUCTION_STORAGE_BUCKET: UPath = {
    "LOCAL": UPath(__file__).parent.parent / "data",
    # TODO: Should we also have a staging bucket for user data?
    "BRANCH": UPath("az://enclaveid-production-bucket/"),
    "PROD": UPath("az://enclaveid-production-bucket/"),
}[DEPLOYMENT_TYPE]

DAGSTER_STORAGE_BUCKET: UPath = {
    "LOCAL": UPath(__file__).parent.parent / "data",
    "BRANCH": UPath("az://enclaveid-dagster-staging-bucket/"),
    "PROD": UPath("az://enclaveid-dagster-prod-bucket/"),
}[DEPLOYMENT_TYPE]

DEPLOYMENT_ROW_LIMIT = {"LOCAL": 100, "BRANCH": None, "PROD": None}[DEPLOYMENT_TYPE]


class DataProvider:
    GOOGLE = {
        "path_prefix": "google",
        "expected_file": "Takeout/My Activity/Search/MyActivity.json",
    }
    FACEBOOK = {
        "path_prefix": "facebook",
        "expected_file": "TODO",
    }
    OPENAI = {
        "path_prefix": "openai",
        "expected_file": "TODO",
    }
