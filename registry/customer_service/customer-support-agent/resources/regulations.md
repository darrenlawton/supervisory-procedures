# Regulatory Obligations — Customer Support Agent

## UK Consumer Duty (FCA PS22/9)

**Agent obligations:**
- Ensure outcomes for customers — responses must be accurate, clear, and genuinely helpful
- Avoid causing foreseeable harm — do not suggest resolutions that disadvantage the customer
- Support customer understanding — use plain English; avoid jargon in all drafted responses
- Act in good faith — do not use urgency tactics or misleading framing in responses

**Key control point:** `regulated-complaint-detected` — any expression of dissatisfaction about a financial product must be routed to the Complaints team under FCA DISP rules.

---

## UK GDPR / Data Protection Act 2018

**Agent obligations:**
- Access only the minimum personal data necessary to resolve the current ticket (data minimisation)
- Do not retain ticket content or personal data beyond the 2-year CRM retention policy
- Do not transfer data to any tool, channel, or third party outside the approved data processing agreement
- Subject Access Requests (SARs) must be immediately escalated to the Data Protection Officer — do not attempt to respond to SARs within the support workflow

**Key control point:** `data-access-scope-breach` — any attempt to access out-of-scope data must halt processing immediately.

---

## Consumer Rights Act 2015

**Agent obligations:**
- Customers are entitled to a refund, repair, or replacement for goods that are faulty, not as described, or not fit for purpose within statutory timeframes:
  - Within 30 days: right to a full refund
  - Within 6 months: presumed fault was present at delivery; repair or replacement first, then refund
  - Up to 6 years: must prove fault existed at time of delivery
- Do not misrepresent the customer's statutory rights (e.g. claiming returns are only possible within a shorter commercial policy window when a statutory right exists)

---

## FCA DISP — Complaints Handling

**Definition of a regulated complaint:**
> An oral or written expression of dissatisfaction, whether justified or not, from or on behalf of an eligible complainant about the firm's provision of, or failure to provide, a financial service or a redress determination, which alleges that the complainant has suffered, or may suffer, financial loss, material distress, or material inconvenience.

**Agent obligations:**
- Immediately route any ticket meeting this definition to the Complaints team
- Do not attempt to resolve a regulated complaint within the standard support workflow
- Log the handoff in the CRM audit trail

**Key control point:** `regulated-complaint-detected`

---

## PCI DSS

**Agent obligations:**
- Never request, store, log, or transmit full payment card numbers (PAN), CVV/CVC codes, or card expiry dates via the support channel
- If a customer shares card details in a message, do not acknowledge or repeat them; advise the customer to use the secure payment portal and flag the ticket for data security review

**Key control point:** `data-access-scope-breach` applies if the agent attempts to retrieve payment card data from the CRM.

---

## Equality Act 2010

**Agent obligations:**
- Do not use age, ethnicity, disability, religion, gender, or other protected characteristics as inputs to ticket priority scoring or resolution selection
- Provide reasonable adjustments on request (e.g. larger-font written responses, simplified language for customers with accessibility needs)
- Route any complaint of discriminatory treatment to the Complaints team
