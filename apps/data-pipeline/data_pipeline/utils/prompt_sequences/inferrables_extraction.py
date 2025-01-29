from textwrap import dedent
from typing import Callable

from data_pipeline.resources.batch_inference.base_llm_resource import PromptSequence


def _get_meta_inference_prompt(chunk: str, user_name: str, partner_name: str) -> str:
    return dedent(
        f"""
        Step 1: Meta Pattern Analysis

        Analyze the conversation between {user_name} and {partner_name} to identify context-independent
        and non-obvious meta patterns in their communication style.

        Focus on patterns such as:
        - Reciprocity in language
        - Future-orientation and planning
        - Affirmation or disagreement patterns
        - Terms of endearment usage
        - Problem-solving language

        Requirements:
        1. Exclude raw message content or obvious information
        2. Keep each observation context-independent
        3. Link to previous relevant nodes using "caused_by"

        Output JSON list of nodes following these rules:
        - Each node should be atomic and represent ONE concept
        - Include datetime information in YYYY-MM-DD HH:MM:SS format (or YYYY-MM-DD if time is ambiguous)
        - Use essential nouns/verbs in the "proposition" field
        - Link to previous nodes using "caused_by" field. A node can have multiple "caused_by" links.
        - Format:
          [
            {{
              "id": "node_label",
              "proposition": "node_proposition",
              "datetime": "proposition_datetime",
              "caused_by": ["list_of_causal_nodes"]
            }},
            ...
          ]

        Example valid propositions:
        - "{partner_name} is comfortable being vulnerable with {user_name}"
        - "{user_name} supports {partner_name}'s understanding with detailed responses"

        Example invalid propositions:
        - "{user_name} deletes a message"
        - "{partner_name} shares an accomplishment"
        - "{user_name} seeks clarification"

        Conversation chunk:
        {chunk}
        """
    ).strip()


def _get_context_inference_prompt(user_name: str, partner_name: str) -> str:
    return dedent(
        f"""
        Step 2: Context Analysis

        Now analyze the broader conversation context considering:
        1. Primary topics/themes
        2. Environmental/situational context
        3. Relationship dynamics
        4. Shared knowledge references

        Produce a JSON like you did before, but this time you should link the new nodes you will extract to the previous step's nodes.

        Requirements:
        1. Each node should represent ONE contextual factor
        2. Use a "caused" field if a new node determines some other nodes in the previous step.
        3. Include only inferences you're confident about.
        4. Make sure to also link contexts that caused each other, using the "caused_by" field.

        For example: {user_name} and {partner_name} are in Italy -> {user_name} is making plans for a dinner date

        IMPORTANT: Return an empty array if it's not possible to infer any context!
        """
    ).strip()


def _get_paritcipant_attributes_inference_prompt(
    user_name: str, partner_name: str
) -> str:
    return dedent(
        f"""
        Step 3: Participant Attributes Inference

        Now infer non-obvious participant attributes that:
        1. Explain communication patterns and/or context
        2. Are not directly observable in raw messages
        3. Can be inferred with confidence, without speculation

        Requirements:
        1. Each node should represent ONE personal characteristic
        2. Reference both attributes and context from previous steps
        3. Use "caused" and "caused_by" to show relationships

        For example if you extract the attribute:
        "{user_name} is very anxious"
        Then it could be "caused_by" the context:
        "{user_name} has messed up their plans in italy"
        And it could have "caused" the meta-pattern:
        "{user_name} is sending multiple messages one after the other to {partner_name}"

        IMPORTANT: Return an empty array if it's not possible to infer any attribute about the participants!
        """
    ).strip()


def get_inferrables_extraction_prompt_sequence(
    chunk: str, user_name: str, partner_name: str
) -> PromptSequence:
    return [
        _get_meta_inference_prompt(chunk, user_name, partner_name),
        _get_context_inference_prompt(user_name, partner_name),
        _get_paritcipant_attributes_inference_prompt(user_name, partner_name),
    ]


if __name__ == "__main__":
    for x in get_inferrables_extraction_prompt_sequence(
        "messages_str", "Giovanni", "Estela"
    ):
        print("-" * 100)
        if isinstance(x, Callable):
            print(x(""))
        else:
            print(x)
