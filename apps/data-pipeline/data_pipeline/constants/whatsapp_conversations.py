from enum import Enum

MIN_WHATSAPP_CONVERSATION_CHUNK_SIZE = 5


class PartnerType(Enum):
    ROMANTIC = "romantic"
    FRIENDSHIP = "friendship"
    FAMILY = "family"
