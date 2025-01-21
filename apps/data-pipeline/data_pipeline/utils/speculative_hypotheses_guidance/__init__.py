from data_pipeline.constants.whatsapp_conversations import PartnerType
from data_pipeline.utils.speculative_hypotheses_guidance.romantic import (
    ROMANTIC_HYPOTHESIS_GUIDANCE_PROMPT_SEGMENT,
)


def get_speculative_hypotheses_guidance(partner_type: PartnerType) -> str:
    if partner_type == PartnerType.ROMANTIC:
        return ROMANTIC_HYPOTHESIS_GUIDANCE_PROMPT_SEGMENT
    else:
        raise NotImplementedError(
            f"No hypothesis guidance for partner type: {partner_type}"
        )
