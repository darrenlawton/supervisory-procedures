# Applicable Regulations — Retail Company Valuation Model

## FCA MAR — Market Abuse Regulation (Insider Information Controls)

The Market Abuse Regulation prohibits the use of inside information (material
non-public information, MNPI) in the preparation or publication of investment
research and valuation work. Using MNPI as a model input constitutes market abuse.

**Agent obligation:** The `inside-information-detected` control point vetoes
processing immediately if any data source is flagged as containing MNPI or
originates from a deal data room. The agent must not retrieve or process
non-public information under any circumstances.

## FCA COBS 12.2 — Research Independence Requirements

Investment research must be produced independently of investment banking activity
and free from conflicts of interest. Research prepared for a company where the
firm has an active M&A mandate is subject to strict information barriers.

**Agent obligation:** The `target-on-restricted-list` control point vetoes
processing if the target company is on the restricted or watch list, preventing
any research or valuation work that could compromise independence. The
`restricted-list-cleared` control point requires explicit Compliance sign-off
before data retrieval begins.

## MiFID II — Conflicts of Interest and Research Objectivity

Under MiFID II, firms must identify and manage conflicts of interest when
producing investment research. Valuation models used for client-facing purposes
must be prepared under controls that prevent conflicts from influencing output.

**Agent obligation:** The agent produces analysis only — it does not generate
final investment recommendations. The Coverage MD `external-sharing-approval`
control point ensures no client-facing output is distributed without explicit
senior authorisation, preventing distribution of conflicted research.
