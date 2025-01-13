import os
from typing import Literal

from upath import UPath


def get_environment() -> Literal["LOCAL", "BRANCH", "PROD"]:
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "prod":
        return "PROD"
    return "LOCAL"


DEPLOYMENT_TYPE = get_environment()

STORAGE_BUCKET: UPath = {
    "LOCAL": UPath(__file__).parent.parent.parent / "data",
    "BRANCH": UPath("az://enclaveid-production-bucket/"),  # TODO
    "PROD": UPath("az://enclaveid-production-bucket/"),
}[DEPLOYMENT_TYPE]


DAGSTER_STORAGE_DIRECTORY = STORAGE_BUCKET / "dagster"
BATCH_STORAGE_DIRECTORY = STORAGE_BUCKET / "batch"
API_STORAGE_DIRECTORY = STORAGE_BUCKET / "api"

DEPLOYMENT_ROW_LIMIT = {"LOCAL": 50, "BRANCH": None, "PROD": None}[DEPLOYMENT_TYPE]


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
        "expected_file": "conversations.json",
    }
    WHATSAPP_DESKTOP = {
        "path_prefix": "whatsapp_desktop",
        "expected_file": "TODO",
    }
    WHATSAPP_MOBILE = {
        "path_prefix": "whatsapp_mobile",
        "expected_file": "TODO",
    }
