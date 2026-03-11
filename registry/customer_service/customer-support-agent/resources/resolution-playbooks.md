# Resolution Playbooks — Customer Support Agent

This document defines the approved resolution playbooks for each ticket category.
The agent must consult these playbooks when determining the appropriate resolution
and drafting customer responses. Resolutions outside these playbooks require
human agent escalation.

---

## 1. Billing & Payments

### 1.1 Duplicate charge
- **Eligibility**: Customer provides order reference; duplicate confirmed in CRM
- **Standard resolution**: Issue full refund to original payment method (within 30-day policy window)
- **Approval required**: No — covered by standard refund policy
- **Response template**: `billing/duplicate-charge-refund`

### 1.2 Unrecognised charge
- **Eligibility**: Charge is within the last 90 days; account is in good standing
- **Standard resolution**: Place charge on hold and escalate to Billing Investigations
- **Approval required**: Yes — route to Level 2 agent via escalation-handoff-review
- **Response template**: `billing/unrecognised-charge-escalation`

### 1.3 Failed payment
- **Eligibility**: Subscription is active; no prior outstanding balance
- **Standard resolution**: Prompt customer to update payment method via self-service portal; provide link
- **Approval required**: No
- **Response template**: `billing/failed-payment-self-service`

---

## 2. Technical Support

### 2.1 Login / access issues
- **Eligibility**: Identity verified via CRM; account not suspended for policy breach
- **Standard resolution**: Unlock account if locked after failed attempts (≤ 10 failed attempts); send password reset link
- **Approval required**: No (unlock only); Yes if account was manually suspended
- **Response template**: `technical/account-unlock`

### 2.2 Feature not working as expected
- **Eligibility**: Bug confirmed in known-issues register, or reproducible from ticket details
- **Standard resolution**: Provide workaround from knowledge base; log bug report if not already tracked
- **Approval required**: No
- **Response template**: `technical/known-issue-workaround`

---

## 3. Returns & Refunds

### 3.1 Return request — within 30-day window
- **Eligibility**: Purchase date ≤ 30 days ago; item unused and in original condition per customer declaration
- **Standard resolution**: Issue prepaid return label; confirm refund will be processed on receipt
- **Approval required**: No
- **Response template**: `returns/standard-return-label`

### 3.2 Return request — outside 30-day window
- **Eligibility**: Purchase date > 30 days; may be eligible under warranty or Consumer Rights Act
- **Standard resolution**: Escalate to Returns Specialist for case-by-case assessment
- **Approval required**: Yes — route to Returns Specialist
- **Response template**: `returns/out-of-window-escalation`

### 3.3 Damaged or incorrect item
- **Eligibility**: Reported within 14 days of delivery; supported by photo evidence or confirmed in order record
- **Standard resolution**: Issue replacement or full refund at customer preference; no return required
- **Approval required**: No (replacement/refund ≤ £100); Yes for high-value items > £100
- **Response template**: `returns/damaged-or-incorrect`

---

## 4. Account Management

### 4.1 Subscription cancellation
- **Eligibility**: Active subscription; no outstanding balance
- **Standard resolution**: Present retention offer (if applicable per current campaign); process cancellation if customer declines or no offer is active
- **Approval required**: Yes — account changes require Level 2 approval
- **Response template**: `account/cancellation-retention`

### 4.2 Account data update (name, email, address)
- **Eligibility**: Customer authenticated; change does not involve payment details
- **Standard resolution**: Direct customer to self-service profile settings; provide step-by-step guide
- **Approval required**: No
- **Response template**: `account/self-service-data-update`

---

## 5. Escalation Criteria

The agent must escalate (generate-escalation-summary) rather than attempt resolution when:

- The ticket type is not covered by any playbook above
- The customer has expressed intent to take legal action or contact a regulator
- The ticket meets the FCA DISP regulated complaint definition (→ Complaints team)
- Sentiment score < -0.7 and the issue is unresolved after the first response
- The required resolution value exceeds the standard compensation threshold (£25 credit; £100 refund)
- Any vetoed control point has fired
