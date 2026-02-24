# Applicable Regulations — Loan Application Processing

## FCA CONC 5.2 — Creditworthiness Assessment

The firm must undertake a reasonable creditworthiness assessment before entering
into a regulated credit agreement. The assessment must consider the potential for
the credit commitment to adversely impact the customer's financial situation.

**Agent obligation:** The agent's recommendation report must include the
creditworthiness assessment inputs (credit score, debt-to-income ratio, income
verification status) so the human underwriter can satisfy this requirement.

## FCA CONC 7.3 — Arrears and Default

Firms must treat customers in arrears or default fairly, including communicating
clearly about the situation and options available.

**Agent obligation:** Templated communications must comply with CONC 7.3 tone
and content requirements. The agent must not send communications that could be
construed as threatening or misleading.

## ICO UK GDPR — Article 22 (Automated Decision-Making)

Where a decision is based solely on automated processing and produces legal or
similarly significant effects, the data subject has the right to human review.

**Agent obligation:** The agent produces a recommendation only. The binding
lending decision is made by a human underwriter. This workflow is designed to
comply with Article 22 by ensuring human review at the `creditworthiness-assessment-review`
checkpoint before any decision is communicated.

## Equality Act 2010 — Protected Characteristics

It is unlawful to discriminate, directly or indirectly, on the basis of protected
characteristics including age (with limited exceptions), race, sex, disability,
religion or belief, sexual orientation, gender reassignment, pregnancy and
maternity, and marriage/civil partnership.

**Agent obligation:** The `protected-characteristic-detected` veto trigger
immediately halts processing if any data source attempts to supply a protected
characteristic as a model feature.
