from typing import Tuple

from json_repair import repair_json


def parse_whatsapp_claims(
    user_name: str, partner_name: str, response: str
) -> Tuple[list[str], list[str]] | Tuple[None, None]:
    try:
        res = repair_json(response, return_objects=True)
        if isinstance(res, dict) and user_name in res and partner_name in res:
            return (
                res[user_name],
                res[partner_name],
            )
        else:
            return (None, None)
    except Exception:
        return (None, None)
