"""Demonstrates workflow-driven execution using the skill's workflow.steps definition.

The supervisor-authored workflow block in the skill YAML defines:
  - The ordered sequence of steps
  - Which veto trigger to evaluate after each step
  - Which oversight checkpoint gates progression after each step

WorkflowRunner reads skill["workflow"]["steps"] at runtime and executes them
in order. The agent provides activity implementations, per-step kwargs,
veto evaluators, and checkpoint handlers — but it does NOT control the sequence.
The sequence is owned by the supervisor.

Run from the project root:
    pip install -e .
    python examples/loan_application_activity_dispatch.py
"""

from __future__ import annotations

import dataclasses
import datetime
from typing import Any, Callable

from supervisory_procedures.core.registry import SkillRegistry


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class VetoTriggeredError(Exception):
    """Raised when a hard_veto_trigger fires during workflow execution."""

    def __init__(self, veto_id: str, action: str, contact: str) -> None:
        self.veto_id = veto_id
        self.action = action
        self.escalation_contact = contact
        msg = f"Veto '{veto_id}' triggered — action: {action}"
        if contact:
            msg += f", escalate to: {contact}"
        super().__init__(msg)


class CheckpointBlockedError(Exception):
    """Raised when an oversight checkpoint does not pass."""

    def __init__(self, checkpoint_id: str, who_reviews: str) -> None:
        self.checkpoint_id = checkpoint_id
        self.who_reviews = who_reviews
        super().__init__(
            f"Checkpoint '{checkpoint_id}' blocked — awaiting review by: {who_reviews}"
        )


# ---------------------------------------------------------------------------
# WorkflowRunner — drives execution from skill["workflow"]["steps"]
# ---------------------------------------------------------------------------

class WorkflowRunner:
    """Executes the workflow defined in the skill YAML.

    The supervisor-authored workflow.steps define the sequence, veto triggers,
    and oversight checkpoints. The agent provides:
      - Activity implementations  via .register(activity, fn)
      - Per-step kwargs            via .set_step_kwargs(step_id, dict | callable)
      - Veto evaluators            via .register_veto(veto_id, fn)
      - Checkpoint handlers        via .register_checkpoint(checkpoint_id, fn)

    Each step's kwargs callable receives the dict of results accumulated so far,
    keyed by step_id — allowing later steps to reference earlier outputs.

    The agent never controls sequencing. If a step is not in workflow.steps,
    it will not be called. If an activity is not in approved_activities, it
    cannot be registered.
    """

    def __init__(self, skill_data: dict[str, Any]) -> None:
        self._skill_id: str = skill_data["metadata"]["id"]
        self._approved: set[str] = set(skill_data["scope"]["approved_activities"])
        self._steps: list[dict] = skill_data["workflow"]["steps"]
        self._veto_index: dict[str, dict] = {
            v["id"]: v for v in skill_data["hard_veto_triggers"]
        }
        self._checkpoint_index: dict[str, dict] = {
            cp["id"]: cp
            for cp in skill_data["oversight_checkpoints"]["workflow_checkpoints"]
        }
        self._activity_registry: dict[str, Callable] = {}
        self._step_kwargs: dict[str, dict | Callable] = {}
        self._veto_evaluators: dict[str, Callable] = {}
        self._checkpoint_handlers: dict[str, Callable] = {}
        self._results: dict[str, Any] = {}
        self._audit_log: list[dict] = []

    def register(self, activity: str, fn: Callable) -> None:
        """Register a callable against an approved_activity string.

        Raises ValueError if the activity is not in the skill's allowlist —
        catching misconfiguration at startup.
        """
        if activity not in self._approved:
            raise ValueError(
                f"Cannot register '{activity}': not in approved_activities "
                f"for skill '{self._skill_id}'"
            )
        self._activity_registry[activity] = fn

    def set_step_kwargs(self, step_id: str, kwargs: dict | Callable) -> None:
        """Provide kwargs for a specific workflow step.

        Pass a plain dict for steps with fixed inputs, or a callable that
        receives the accumulated results dict and returns a dict — for steps
        whose inputs depend on earlier step outputs.
        """
        self._step_kwargs[step_id] = kwargs

    def register_veto(self, veto_id: str, fn: Callable) -> None:
        """Register an evaluator for a hard_veto_trigger.

        fn(step_result, all_results) -> bool. Returns True if the veto fires.
        """
        self._veto_evaluators[veto_id] = fn

    def register_checkpoint(self, checkpoint_id: str, fn: Callable) -> None:
        """Register a handler for an oversight checkpoint.

        fn(step_result, all_results, checkpoint_def) -> bool.
        Returns True to allow progression, False to block.
        """
        self._checkpoint_handlers[checkpoint_id] = fn

    def execute(self) -> dict[str, Any]:
        """Execute all workflow steps in the order defined by the skill YAML.

        Returns the accumulated results dict (step_id → return value).
        Raises VetoTriggeredError or CheckpointBlockedError on governance failures.
        """
        for step in self._steps:
            step_id = step["id"]
            activity = step["activity"]

            # Resolve per-step kwargs — callable form allows referencing prior results
            raw = self._step_kwargs.get(step_id, {})
            kwargs: dict = raw(self._results) if callable(raw) else raw

            # Execute the registered activity function
            fn = self._activity_registry[activity]
            result = fn(**kwargs)
            self._results[step_id] = result

            self._audit_log.append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "skill_id": self._skill_id,
                "step_id": step_id,
                "activity": activity,
                "status": "completed",
            })

            # Evaluate veto trigger (if defined for this step)
            if veto_id := step.get("veto_trigger"):
                veto_def = self._veto_index[veto_id]
                evaluator = self._veto_evaluators.get(veto_id)
                if evaluator and evaluator(result, self._results):
                    raise VetoTriggeredError(
                        veto_id,
                        veto_def["action"],
                        veto_def.get("escalation_contact", ""),
                    )

            # Evaluate oversight checkpoint (if defined for this step)
            if cp_id := step.get("checkpoint"):
                cp_def = self._checkpoint_index[cp_id]
                handler = self._checkpoint_handlers.get(cp_id)
                if handler and not handler(result, self._results, cp_def):
                    raise CheckpointBlockedError(cp_id, cp_def["who_reviews"])

        return self._results

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
    print(f"  [credit] Querying credit score for {applicant_name}...")
    return {
        "credit_score": 712,
        "band": "good",
        "default_probability": 0.032,
        "open_accounts": 3,
        "adverse_markers": 0,
    }


def run_sanctions_screening(applicant_name: str, date_of_birth: str, address: str) -> dict:
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
    print(f"  [email] Sending '{status}' email to {applicant_name}...")
    templates = {
        "received":    "Your application {id} has been received and is under review.",
        "in_progress": "Your application {id} is progressing — we will contact you shortly.",
        "decision":    "A decision has been reached on your application {id}.",
    }
    body = templates.get(status, "Your application {id} has been updated.").format(id=application_id)
    return {"sent": True, "to": applicant_name, "template": status, "body": body}


def log_audit_entry(event: str, application_id: str, detail: str) -> dict:
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "application_id": application_id,
        "event": event,
        "detail": detail,
    }
    print(f"  [audit] {entry['timestamp']} | {event} | {detail[:60]}")
    return entry


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def main() -> None:
    application_id = "APP-2025-00142"
    requested_loan_gbp = 18_500.0

    # 1. Load the skill — access control enforced by registry
    registry = SkillRegistry()
    skill = registry.get_skill(
        "retail_banking/loan-application-processing",
        agent_id="loan-processor-agent-prod",
    )
    runner = WorkflowRunner(skill)

    # 2. Register activity implementations
    #    Each string must match exactly an entry in scope.approved_activities.
    runner.register(
        "Retrieve and parse submitted application documents (proof of income, ID)",
        retrieve_and_parse_documents,
    )
    runner.register(
        "Query the internal credit scoring system for the applicant's risk score",
        query_credit_scoring_system,
    )
    runner.register(
        "Cross-reference applicant details against the sanctions screening database",
        run_sanctions_screening,
    )
    runner.register(
        "Calculate debt-to-income ratio using declared and verified income figures",
        calculate_debt_to_income_ratio,
    )
    runner.register(
        "Generate a structured recommendation report for the human underwriter",
        generate_recommendation_report,
    )
    runner.register(
        "Send templated acknowledgement and status-update emails to the applicant",
        send_acknowledgement_email,
    )
    runner.register(
        "Log all actions and data accesses to the audit trail",
        log_audit_entry,
    )

    # 3. Provide per-step kwargs.
    #    Fixed inputs use a plain dict. Steps that depend on earlier outputs
    #    use a callable that receives the accumulated results dict.
    runner.set_step_kwargs("retrieve-documents", {"application_id": application_id})

    runner.set_step_kwargs("log-documents-retrieved", lambda r: {
        "event": "documents_retrieved",
        "application_id": application_id,
        "detail": (
            f"ID type: {r['retrieve-documents'].id_document_type}, "
            f"verified sources: {r['retrieve-documents'].id_verified_sources}"
        ),
    })

    runner.set_step_kwargs("sanctions-screening", lambda r: {
        "applicant_name": r["retrieve-documents"].applicant_name,
        "date_of_birth":  r["retrieve-documents"].date_of_birth,
        "address":        r["retrieve-documents"].address,
    })

    runner.set_step_kwargs("log-sanctions-complete", lambda r: {
        "event": "sanctions_screening_complete",
        "application_id": application_id,
        "detail": (
            f"match_found={r['sanctions-screening']['match_found']}, "
            f"confidence={r['sanctions-screening']['match_confidence']}"
        ),
    })

    runner.set_step_kwargs("credit-score", lambda r: {
        "applicant_name": r["retrieve-documents"].applicant_name,
        "date_of_birth":  r["retrieve-documents"].date_of_birth,
    })

    runner.set_step_kwargs("log-credit-retrieved", lambda r: {
        "event": "credit_score_retrieved",
        "application_id": application_id,
        "detail": (
            f"score={r['credit-score']['credit_score']}, "
            f"band={r['credit-score']['band']}"
        ),
    })

    runner.set_step_kwargs("calculate-dti", lambda r: {
        "verified_income_gbp":              r["retrieve-documents"].verified_income_gbp,
        "requested_loan_gbp":               requested_loan_gbp,
        "existing_monthly_obligations_gbp": 320.0,
    })

    runner.set_step_kwargs("log-dti-calculated", lambda r: {
        "event": "dti_calculated",
        "application_id": application_id,
        "detail": (
            f"dti={r['calculate-dti']['dti_ratio']}, "
            f"within_policy={r['calculate-dti']['dti_within_policy']}"
        ),
    })

    runner.set_step_kwargs("send-progress-notification", lambda r: {
        "applicant_name": r["retrieve-documents"].applicant_name,
        "application_id": application_id,
        "status": "in_progress",
    })

    runner.set_step_kwargs("generate-recommendation", lambda r: {
        "application_id":   application_id,
        "documents":        r["retrieve-documents"],
        "credit_result":    r["credit-score"],
        "sanctions_result": r["sanctions-screening"],
        "dti_result":       r["calculate-dti"],
        "requested_loan_gbp": requested_loan_gbp,
    })

    runner.set_step_kwargs("log-recommendation-generated", lambda r: {
        "event": "recommendation_generated",
        "application_id": application_id,
        "detail": (
            f"recommendation={r['generate-recommendation']['recommendation']}, "
            f"awaiting_approval=True"
        ),
    })

    runner.set_step_kwargs("notify-applicant-decision", lambda r: {
        "applicant_name": r["retrieve-documents"].applicant_name,
        "application_id": application_id,
        "status": "decision",
    })

    # 4. Register veto evaluators.
    #    Each evaluator receives (step_result, all_results) and returns True to fire.
    runner.register_veto(
        "data-quality-critical",
        lambda result, _: result is None,
    )
    runner.register_veto(
        "sanctions-match",
        lambda result, _: result["match_found"] or result["exact_match"],
    )
    runner.register_veto(
        "protected-characteristic-detected",
        lambda result, _: False,  # not surfaced by stub credit bureau
    )

    # 5. Register checkpoint handlers.
    #    Each handler receives (step_result, all_results, checkpoint_def)
    #    and returns True to allow progression.
    runner.register_checkpoint(
        "identity-verified",
        lambda result, _, cp: result.id_verified_sources >= 2,
    )
    runner.register_checkpoint(
        "creditworthiness-assessment-review",
        lambda result, _, cp: (
            # Simulated underwriter approval — in production this would
            # pause and await a human response via a task queue or UI.
            print(f"  [checkpoint] {cp['name']} — simulating underwriter approval") or True
        ),
    )
    runner.register_checkpoint(
        "decision-communication",
        lambda result, _, cp: (
            print(f"  [checkpoint] {cp['name']} — notifying applicant") or True
        ),
    )

    # 6. Execute — the runner drives the sequence from skill["workflow"]["steps"]
    print(f"\nProcessing application {application_id} (£{requested_loan_gbp:,.0f} loan)")
    print(f"Workflow: {len(skill['workflow']['steps'])} steps as defined in skill YAML\n")

    try:
        results = runner.execute()
    except VetoTriggeredError as exc:
        print(f"\n  HARD VETO: {exc}")
        return
    except CheckpointBlockedError as exc:
        print(f"\n  CHECKPOINT BLOCKED: {exc}")
        return

    report = results["generate-recommendation"]
    print(f"\n  Recommendation: {report['recommendation']}")
    print(f"  Credit score:   {report['credit_score']}")
    print(f"  DTI ratio:      {report['dti_ratio']} ({'within policy' if report['dti_within_policy'] else 'exceeds policy'})")
    print(f"  Sanctions:      {'clear' if report['sanctions_clear'] else 'MATCH FOUND'}")
    print(f"  Identity:       {'verified' if report['identity_verified'] else 'UNVERIFIED'}")
    if report["issues"]:
        for issue in report["issues"]:
            print(f"  Issue:          {issue}")
    print(f"\n  Report is awaiting underwriter approval — agent workflow complete.")

    # 7. Demonstrate that the allowlist is still enforced at registration
    print("\n--- Attempting to register a non-approved activity ---")
    try:
        runner.register(
            "Access the applicant's full transaction history",
            lambda **kw: None,
        )
    except ValueError as exc:
        print(f"  BLOCKED at registration: {exc}")

    # 8. Show audit log — every step recorded, driven by the workflow definition
    print("\n--- Audit log ---")
    for entry in runner.audit_log:
        print(f"  {entry['timestamp']}  [{entry['step_id']}]  {entry['activity'][:55]}")


if __name__ == "__main__":
    main()
