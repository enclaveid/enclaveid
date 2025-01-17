# TODO
from data_pipeline.constants.environments import get_environment

MIN_HUMAN_CONVERSATION_CHUNK_SIZE = 10


def get_messaging_partners_names() -> dict[str, str]:
    if get_environment() == "LOCAL":
        return {
            "me": "Giovanni",
            "partner": "Estela",
        }

    raise NotImplementedError("Partner name not implemented for non-local environments")
