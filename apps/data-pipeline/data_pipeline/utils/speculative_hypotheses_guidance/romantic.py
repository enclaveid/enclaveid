from data_pipeline.constants.whatsapp_conversations import PartnerType

ROMANTIC_HYPOTHESIS_GUIDANCE_PROMPT_SEGMENT = f"""
The relationship between the two partners is of {PartnerType.ROMANTIC} type, try to extract hypotheses relevant to these aspects:
- Attachment & Trauma - Consider how early relationships and past traumatic experiences might shape current reactions and expectations around emotional safety, intimacy, and conflict.
- Family & Cultural Systems - Examine how learned patterns from family of origin and cultural background influence relationship expectations, roles, and communication styles.
- Identity & Development - Assess how each partner's sense of self, developmental stage, and individual growth journey impacts their approach to the relationship.
- Regulation & Coping - Look for patterns in how partners manage difficult emotions, stress, and vulnerability, both individually and as a system.
- Power & Control Dynamics - Analyze how behaviors might function to maintain or challenge relationship power balances, including both overt and subtle manifestations.
- Unmet Core Needs - Identify fundamental emotional and relational needs that may be expressed indirectly through surface behaviors and conflicts.
- Meta-Communication Patterns - Observe recurring cycles in how partners exchange information, emotions, and meaning beyond the content level.
- External & Physiological Factors - Consider how outside stressors, health conditions, and biological factors may manifest in relationship dynamics.
"""
