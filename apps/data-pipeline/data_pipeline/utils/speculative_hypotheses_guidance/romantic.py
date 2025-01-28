from data_pipeline.constants.whatsapp_conversations import PartnerType

ROMANTIC_HYPOTHESIS_GUIDANCE_PROMPT_SEGMENT = f"""
The relationship between the two partners is of {PartnerType.ROMANTIC.value} type, try to extract hypotheses relevant to these aspects:
- Attachment & Trauma - Consider how early relationships and past traumatic experiences might shape current reactions and expectations around emotional safety, intimacy, and conflict.
- Family & Cultural Systems - Examine how learned patterns from family of origin and cultural background influence relationship expectations, roles, and communication styles.
- Identity & Development - Assess how each partner's sense of self, developmental stage, and individual growth journey impacts their approach to the relationship.
- Regulation & Coping - Look for patterns in how partners manage difficult emotions, stress, and vulnerability, both individually and as a system.
- Power & Control Dynamics - Analyze how behaviors might function to maintain or challenge relationship power balances, including both overt and subtle manifestations.
- Unmet Core Needs - Identify fundamental emotional and relational needs that may be expressed indirectly through surface behaviors and conflicts.
- Meta-Communication Patterns - Observe recurring cycles in how partners exchange information, emotions, and meaning beyond the content level.
- External & Physiological Factors - Consider how outside stressors, health conditions, and biological factors may manifest in relationship dynamics.
"""

ROMANTIC_INFERENCE_GUIDANCE_PROMPT_SEGMENT = f"""
The relationship between the two partners is of {PartnerType.ROMANTIC.value} type, so try to make inferences relevant to these aspects:
- Reciprocity in language: When one person uses certain phrases or topics and whether/how quickly the other person engages with those same elements in their response, acknowledging it.
- Future-oriented language: Planning words and future tense indicate how much each person initiates future plans.
- Affirmation patterns: Agreement versus disagreement or hesitation from each person.
- Terms of endearment usage: Overall frequency and consistency of affectionate language from each partner.
- Problem-solving language: How often each person brings up issues versus how often they propose solutions
"""
