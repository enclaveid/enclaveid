from typing import Sequence

from pydantic import BaseModel
from upath import UPath

from data_pipeline.constants.environments import API_STORAGE_DIRECTORY, DataProvider
from data_pipeline.constants.whatsapp_conversations import PartnerType
from data_pipeline.resources.postgres_resource import PostgresResource


class MessagingPartners(BaseModel):
    initiator_user_id: str
    initiator_name: str
    initiator_phone_number: str
    partner_user_id: str
    partner_name: str
    partner_phone_number: str
    partner_type: PartnerType


def get_messaging_partners(
    postgres: PostgresResource, phone_numbers: Sequence[str]
) -> MessagingPartners:
    if len(phone_numbers) != 2:
        raise ValueError(
            f"Expected 2 phone numbers, got {len(phone_numbers)}: {phone_numbers}"
        )

    # Query to retrieve userId, phoneNumber, and the corresponding user name.
    results = postgres.execute_query(
        """
        SELECT pn."userId", pn."phoneNumber", u."name"
        FROM "PhoneNumber" pn
        JOIN "User" u ON u.id = pn."userId"
        WHERE pn."phoneNumber" = ANY(%(phone_numbers)s)
        """,
        {"phone_numbers": phone_numbers},
    )

    if len(results) != 2:
        raise ValueError(
            f"Expected exactly 2 phone number records, got {len(results)}. "
            "Please ensure both phone numbers exist in the database."
        )

    # Build a mapping from user_id to their data (phone number and name).
    user_data = {}
    for result in results:
        uid = result["userId"]
        phone = result["phoneNumber"]
        name = result["name"]
        user_data[uid] = {"phone": phone, "name": name}

    if len(user_data) != 2:
        raise ValueError(
            "Both phone numbers belong to the same user; expected two distinct users."
        )

    # Determine which user uploaded a file most recently.
    file_times = {}
    for user_id in user_data:
        file_path: UPath = (
            API_STORAGE_DIRECTORY
            / user_id
            / DataProvider.WHATSAPP_DESKTOP["path_prefix"]
            / "latest.json"
        )
        if file_path.exists():
            file_times[user_id] = file_path.stat().st_mtime
        else:
            # If file does not exist, consider the file time as 0.
            file_times[user_id] = 0

    if all(time == 0 for time in file_times.values()):
        raise ValueError(
            f"No existing files found for any user IDs: {list(user_data.keys())}"
        )

    # The user with the highest file modification time is "me".
    initiator_user_id = max(file_times, key=lambda uid: file_times[uid])
    # The other user is the messaging partner.
    partner_user_id = next(uid for uid in user_data if uid != initiator_user_id)

    messaging_partners = MessagingPartners(
        initiator_user_id=initiator_user_id,
        initiator_name=user_data[initiator_user_id]["name"],
        initiator_phone_number=user_data[initiator_user_id]["phone"],
        partner_user_id=partner_user_id,
        partner_name=user_data[partner_user_id]["name"],
        partner_phone_number=user_data[partner_user_id]["phone"],
        partner_type=PartnerType.ROMANTIC,  # TODO
    )

    return messaging_partners
