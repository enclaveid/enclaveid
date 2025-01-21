from pydantic import BaseModel

from data_pipeline.constants.environments import get_environment
from data_pipeline.constants.whatsapp_conversations import PartnerType


class MessagingPartners(BaseModel):
    me: str
    partner: str
    partner_type: PartnerType


def get_messaging_partners() -> MessagingPartners:
    if get_environment() == "LOCAL":
        return MessagingPartners(
            me="Giovanni",
            partner="Estela",
            partner_type=PartnerType.ROMANTIC,
        )

    raise NotImplementedError("Partner name not implemented for non-local environments")
