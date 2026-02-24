# Applicable Regulations — Sanctions and PEP Alert Review

## BSA/AML — Bank Secrecy Act / Anti-Money Laundering

The Bank Secrecy Act requires financial institutions to implement effective
anti-money laundering programmes, including customer due diligence and sanctions
screening as part of onboarding and ongoing monitoring.

**Agent obligation:** The agent must complete all steps in the SOP checklist
before issuing any recommendation. The `data-source-unavailable` control point
halts processing if mandatory screening lists cannot be accessed.

## OFAC / HM Treasury / EU Consolidated Sanctions Lists

Financial institutions are prohibited from conducting business with individuals
or entities on government sanctions lists. Screening against OFAC SDN, HM
Treasury, and EU Consolidated Lists is mandatory for customer onboarding.

**Agent obligation:** The `exact-sanctions-list-match` control point vetoes
processing immediately if a high-confidence exact match is found. No agent or
human action can override a vetoed control point — escalation to the Financial
Crime team is mandatory.

## FATF Recommendations — Politically Exposed Persons

FATF guidance requires enhanced due diligence for Politically Exposed Persons.
Firms must have risk-based procedures for identifying and managing PEP
relationships, including ongoing monitoring.

**Agent obligation:** PEP hits must be classified using the same three-dimension
matching process (name, DOB, location) and must be reviewed by a qualified
compliance officer before any onboarding decision is made.

## Fed/OCC SR 11-7 — Model Risk Management

Regulators require financial institutions to manage the risk that AI and model
outputs influence decisions in ways that produce adverse outcomes. Models must
be validated, monitored for performance drift, and subject to human oversight.

**Agent obligation:** The `model-accuracy-deviation` control point notifies the
AI Operations Team when performance metrics deviate from validated baselines.
All agent recommendations are advisory only — final disposition is always made
by a qualified human compliance officer.

## ECOA — Equal Credit Opportunity Act

Decisions that affect access to financial products must not be based on
protected characteristics including race, religion, national origin, sex,
marital status, or age.

**Agent obligation:** The agent must not use nationality, ethnicity, religion,
or other protected characteristics as a basis for flagging or clearing a hit.
