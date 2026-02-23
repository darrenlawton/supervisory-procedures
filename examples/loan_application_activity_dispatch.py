"""Demonstrates how approved_activities link to Python functions via ActivityGuard.

Each string in scope.approved_activities is the human-readable name for a permitted
operation. At runtime, the agent maps that string to a concrete Python callable through
an ActivityGuard. Attempting to call any function NOT registered to an approved activity
raises ActivityNotPermittedError — the skill's allowlist is enforced in code.

Run from the project root:
    pip install -e .
    python examples/loan_application_activity_dispatch.py
"""

from __future__ import annotations

import dataclasses
import datetime
import textwrap
from typing import Any, Callable

from supervisory_procedures.core.registry import SkillRegistry


# ---------------------------------------------------------------------------
# ActivityGuard — binds approved_activities strings to callables
# ---------------------------------------------------------------------------

class ActivityNotPermittedError(PermissionError):
    """Raised when an agent attempts to call a function that has no corresponding
    approved_activity in the loaded skill."""

    def __init__(self, activity: str, skill_id: str) -> None:
        super().__init__(
            f"Activity '{activity}' is not listed in approved_activities "
            f"for skill '{skill_id}'. Agent may not perform this action."
        )


class ActivityGuard:
    """Binds approved_activities strings to Python callables.

    Provides a single entry point — .run(activity_name, **kwargs) — that:
      1. Checks the activity string is in the skill's approved_activities list.
      2. Looks up the registered callable.
      3. Calls it, logging each invocation for the audit trail.

    Any function called outside of .run() bypasses governance; that is intentional
    — agents should only call functions through the guard.
    """

    def __init__(self, skill_data: dict[str, Any]) -> None:
        self._skill_id: str = skill_data["metadata"]["id"]
        self._approved: set[str] = set(skill_data["scope"]["approved_activities"])
        self._registry: dict[str, Callable] = {}
        self._audit_log: list[dict] = []

    def register(self, activity: str, fn: Callable) -> None:
        """Register a callable against an approved_activity string.

        Raises ValueError if the activity string is not in the skill's allowlist,
        catching misconfiguration at startup rather than at runtime.
        """
        if activity not in self._approved:
            raise ValueError(
                f"Cannot register '{activity}': not in approved_activities "
                f"for skill '{self._skill_id}'"
            )
        self._registry[activity] = fn

    def run(self, activity: str, **kwargs: Any) -> Any:
        """Execute the function registered for activity, enforcing the allowlist.

        Raises:
            ActivityNotPermittedError: if the activity is not approved.
            KeyError: if the activity is approved but no function has been registered.
        """
        if activity not in self._approved:
            raise ActivityNotPermittedError(activity, self._skill_id)

        fn = self._registry[activity]
        result = fn(**kwargs)

        self._audit_log.append({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "skill_id": self._skill_id,
            "activity": activity,
            "status": "completed",
        })
        return result

    @property
    def audit_log(self) -> list[dict]:
        return list(self._audit_log)


# ---------------------------------------------------------------------------
# Stub implementations — one function per approved_activity
# ---------------------------------------------------------------------------
# In production these would call real services. Here they return plausible
# fake data so the example runs end-to-end without external dependencies.

@dataclasses.dataclass
class ApplicationDocuments:
    applicant_name: str
    date_of_birth: str
    address: str
    declared_income_gbp: float
    verified_income_gbp: float
    employment_status: str
    id_document_type: str
    id_verified_sources: int  # number of independent sources


def retrieve_and_parse_documents(application_id: str) -> ApplicationDocuments:
    """Approved activity: Retrieve and parse submitted application documents (proof of income, ID)"""
    print(f"  [docs] Retrieving documents for application {application_id}...")
    return ApplicationDocuments(
        applicant_name="Jane Smith",
        date_of_birth="1985-04-12",
        address="14 Maple Street, London, EC1A 1BB",
        declared_income_gbp=52_000.0,
        verified_income_gbp=51_200.0,
        employment_status="full-time",
        id_document_type="passport",
        id_verified_sources=2,
    )


def query_credit_scoring_system(applicant_name: str, date_of_birth: str) -> dict:
    """Approved activity: Query the internal credit scoring system for the applicant's risk score"""
    print(f"  [credit] Querying credit score for {applicant_name}...")
    return {
        "credit_score": 712,
        "band": "good",
        "default_probability": 0.032,
        "open_accounts": 3,
        "adverse_markers": 0,
    }


def run_sanctions_screening(applicant_name: str, date_of_birth: str, address: str) -> dict:
    """Approved activity: Cross-reference applicant details against the sanctions screening database"""
    print(f"  [sanctions] Screening {applicant_name} against HM Treasury / OFAC lists...")
    return {
        "match_found": False,
        "exact_match": False,
        "match_confidence": 0.0,
        "lists_checked": ["HM Treasury Consolidated", "OFAC SDN"],
    }


def calculate_debt_to_income_ratio(
    verified_income_gbp: float,
    requested_loan_gbp: float,
    existing_monthly_obligations_gbp: float,
) -> dict:
    """Approved activity: Calculate debt-to-income ratio using declared and verified income figures"""
    print("  [dti] Calculating debt-to-income ratio...")
    monthly_income = verified_income_gbp / 12
    proposed_monthly_repayment = requested_loan_gbp / 60  # assume 5-year term
    total_monthly_obligations = existing_monthly_obligations_gbp + proposed_monthly_repayment
    dti_ratio = total_monthly_obligations / monthly_income
    return {
        "monthly_income_gbp": round(monthly_income, 2),
        "proposed_repayment_gbp": round(proposed_monthly_repayment, 2),
        "total_obligations_gbp": round(total_monthly_obligations, 2),
        "dti_ratio": round(dti_ratio, 3),
        "dti_within_policy": dti_ratio <= 0.45,
    }


def generate_recommendation_report(
    application_id: str,
    documents: ApplicationDocuments,
    credit_result: dict,
    sanctions_result: dict,
    dti_result: dict,
    requested_loan_gbp: float,
) -> dict:
    """Approved activity: Generate a structured recommendation report for the human underwriter"""
    print("  [report] Generating underwriter recommendation report...")
    issues = []
    if not dti_result["dti_within_policy"]:
        issues.append(f"DTI ratio {dti_result['dti_ratio']} exceeds 0.45 policy limit")
    if credit_result["credit_score"] < 580:
        issues.append(f"Credit score {credit_result['credit_score']} below minimum threshold")

    recommendation = "APPROVE" if not issues else "REFER"

    return {
        "application_id": application_id,
        "applicant": documents.applicant_name,
        "requested_loan_gbp": requested_loan_gbp,
        "recommendation": recommendation,
        "credit_score": credit_result["credit_score"],
        "dti_ratio": dti_result["dti_ratio"],
        "dti_within_policy": dti_result["dti_within_policy"],
        "sanctions_clear": not sanctions_result["match_found"],
        "identity_verified": documents.id_verified_sources >= 2,
        "issues": issues,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "awaiting_underwriter_approval": True,
    }


def send_acknowledgement_email(applicant_name: str, application_id: str, status: str) -> dict:
    """Approved activity: Send templated acknowledgement and status-update emails to the applicant"""
    print(f"  [email] Sending '{status}' email to {applicant_name}...")
    templates = {
        "received":    "Your application {id} has been received and is under review.",
        "in_progress": "Your application {id} is progressing — we will contact you shortly.",
    }
    body = templates.get(status, "Your application {id} has been updated.").format(id=application_id)
    return {"sent": True, "to": applicant_name, "template": status, "body": body}


def log_audit_entry(event: str, application_id: str, detail: str) -> dict:
    """Approved activity: Log all actions and data accesses to the audit trail"""
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "application_id": application_id,
        "event": event,
        "detail": detail,
    }
    print(f"  [audit] {entry['timestamp']} | {event} | {detail[:60]}")
    return entry


# ---------------------------------------------------------------------------
# A function that is NOT in approved_activities — to demonstrate the block
# ---------------------------------------------------------------------------

def issue_loan_offer_directly(applicant_name: str, amount_gbp: float) -> None:
    """NOT an approved activity — the skill explicitly prohibits issuing a loan
    offer without underwriter approval. Calling this through the guard will raise."""
    print(f"  Issuing loan offer of £{amount_gbp:,.0f} to {applicant_name}...")


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Load the skill and build an ActivityGuard
    registry = SkillRegistry()
    skill = registry.get_skill(
        "retail_banking/loan-application-processing",
        agent_id="loan-processor-agent-prod",
    )
    guard = ActivityGuard(skill)

    # 2. Register each approved_activity string → Python function
    #    The string must match exactly what is in the YAML.
    guard.register(
        "Retrieve and parse submitted application documents (proof of income, ID)",
        retrieve_and_parse_documents,
    )
    guard.register(
        "Query the internal credit scoring system for the applicant's risk score",
        query_credit_scoring_system,
    )
    guard.register(
        "Cross-reference applicant details against the sanctions screening database",
        run_sanctions_screening,
    )
    guard.register(
        "Calculate debt-to-income ratio using declared and verified income figures",
        calculate_debt_to_income_ratio,
    )
    guard.register(
        "Generate a structured recommendation report for the human underwriter",
        generate_recommendation_report,
    )
    guard.register(
        "Send templated acknowledgement and status-update emails to the applicant",
        send_acknowledgement_email,
    )
    guard.register(
        "Log all actions and data accesses to the audit trail",
        log_audit_entry,
    )

    # 3. Run the loan processing workflow via the guard
    application_id = "APP-2025-00142"
    requested_loan_gbp = 18_500.0

    print(f"\nProcessing application {application_id} (£{requested_loan_gbp:,.0f} loan)\n")

    # Step 1: retrieve documents
    docs = guard.run(
        "Retrieve and parse submitted application documents (proof of income, ID)",
        application_id=application_id,
    )
    guard.run(
        "Log all actions and data accesses to the audit trail",
        event="documents_retrieved",
        application_id=application_id,
        detail=f"ID type: {docs.id_document_type}, verified sources: {docs.id_verified_sources}",
    )

    # Check identity gate (procedural requirement)
    if docs.id_verified_sources < 2:
        print("\n  VETO: Identity not verified against two independent sources — halting.")
        return

    # Step 2: sanctions screening (must run before credit check per procedural requirements)
    sanctions = guard.run(
        "Cross-reference applicant details against the sanctions screening database",
        applicant_name=docs.applicant_name,
        date_of_birth=docs.date_of_birth,
        address=docs.address,
    )
    guard.run(
        "Log all actions and data accesses to the audit trail",
        event="sanctions_screening_complete",
        application_id=application_id,
        detail=f"match_found={sanctions['match_found']}, confidence={sanctions['match_confidence']}",
    )

    if sanctions["match_found"] or sanctions["exact_match"]:
        print("\n  HARD VETO: Sanctions match — halting and escalating to Financial Crime team.")
        return

    # Step 3: credit score
    credit = guard.run(
        "Query the internal credit scoring system for the applicant's risk score",
        applicant_name=docs.applicant_name,
        date_of_birth=docs.date_of_birth,
    )
    guard.run(
        "Log all actions and data accesses to the audit trail",
        event="credit_score_retrieved",
        application_id=application_id,
        detail=f"score={credit['credit_score']}, band={credit['band']}",
    )

    # Step 4: DTI calculation
    dti = guard.run(
        "Calculate debt-to-income ratio using declared and verified income figures",
        verified_income_gbp=docs.verified_income_gbp,
        requested_loan_gbp=requested_loan_gbp,
        existing_monthly_obligations_gbp=320.0,
    )
    guard.run(
        "Log all actions and data accesses to the audit trail",
        event="dti_calculated",
        application_id=application_id,
        detail=f"dti={dti['dti_ratio']}, within_policy={dti['dti_within_policy']}",
    )

    # Step 5: acknowledgement email
    guard.run(
        "Send templated acknowledgement and status-update emails to the applicant",
        applicant_name=docs.applicant_name,
        application_id=application_id,
        status="in_progress",
    )

    # Step 6: recommendation report
    report = guard.run(
        "Generate a structured recommendation report for the human underwriter",
        application_id=application_id,
        documents=docs,
        credit_result=credit,
        sanctions_result=sanctions,
        dti_result=dti,
        requested_loan_gbp=requested_loan_gbp,
    )
    guard.run(
        "Log all actions and data accesses to the audit trail",
        event="recommendation_generated",
        application_id=application_id,
        detail=f"recommendation={report['recommendation']}, awaiting_approval=True",
    )

    print(f"\n  Recommendation: {report['recommendation']}")
    print(f"  Credit score:   {report['credit_score']}")
    print(f"  DTI ratio:      {report['dti_ratio']} ({'within policy' if report['dti_within_policy'] else 'exceeds policy'})")
    print(f"  Sanctions:      {'clear' if report['sanctions_clear'] else 'MATCH FOUND'}")
    print(f"  Identity:       {'verified' if report['identity_verified'] else 'UNVERIFIED'}")
    if report["issues"]:
        for issue in report["issues"]:
            print(f"  Issue:          {issue}")
    print(f"\n  Report is awaiting underwriter approval — agent workflow complete.")

    # 4. Demonstrate the block: attempting a prohibited action through the guard
    print("\n--- Attempting a prohibited action ---")
    try:
        guard.run(
            "Issue a loan offer or rejection directly to the applicant without underwriter approval",
            applicant_name=docs.applicant_name,
            amount_gbp=requested_loan_gbp,
        )
    except ActivityNotPermittedError as exc:
        print(f"  BLOCKED: {exc}")

    # 5. Demonstrate the block: attempting to register a non-approved function
    print("\n--- Attempting to register a non-approved function ---")
    try:
        guard.register(
            "Access the applicant's full transaction history",
            lambda **kw: None,
        )
    except ValueError as exc:
        print(f"  BLOCKED at registration: {exc}")

    # 6. Show audit log
    print("\n--- Audit log ---")
    for entry in guard.audit_log:
        print(f"  {entry['timestamp']}  {entry['activity'][:70]}")


if __name__ == "__main__":
    main()
