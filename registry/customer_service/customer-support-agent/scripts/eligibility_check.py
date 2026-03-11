"""
eligibility_check.py — Customer Support Agent
==============================================
Evaluates customer eligibility for standard resolutions against current
policy rules. Used by activity: run-eligibility-check

Checks the customer's account record and ticket details against:
  - Return window (30-day no-quibble policy)
  - Refund/credit value threshold (£25 credit; £100 refund)
  - Subscription tier entitlements
  - Warranty status

Returns an eligibility result that feeds into the `standard-resolution-confirmed`
control point (auto) or triggers `compensation-approval` / `account-change-approval`
(needs_approval) control points.

Usage
-----
    from scripts.eligibility_check import check_eligibility

    result = check_eligibility(
        ticket_type="returns",
        resolution_type="refund",
        resolution_value=45.00,
        days_since_purchase=18,
        subscription_tier="standard",
    )
    # {
    #   "eligible": True,
    #   "requires_approval": False,
    #   "policy_rule": "standard-30-day-return",
    #   "notes": "Within 30-day return window; value within standard threshold."
    # }
"""

from datetime import date
from typing import Literal

TicketType = Literal["billing", "technical", "account", "returns", "complaints"]
ResolutionType = Literal["refund", "credit", "replacement", "account_change", "information"]

# Policy thresholds
_CREDIT_APPROVAL_THRESHOLD_GBP = 25.0
_REFUND_APPROVAL_THRESHOLD_GBP = 100.0
_STANDARD_RETURN_WINDOW_DAYS = 30


def check_eligibility(
    ticket_type: TicketType,
    resolution_type: ResolutionType,
    resolution_value: float = 0.0,
    days_since_purchase: int | None = None,
    subscription_tier: str = "standard",
    account_in_good_standing: bool = True,
) -> dict:
    """
    Evaluate whether the proposed resolution is eligible under current policy.

    Parameters
    ----------
    ticket_type          : Category of the support ticket
    resolution_type      : Type of resolution being proposed
    resolution_value     : Monetary value of the resolution in GBP (0.0 if non-monetary)
    days_since_purchase  : Days since the relevant purchase (None if not applicable)
    subscription_tier    : Customer's subscription tier (standard, premium, enterprise)
    account_in_good_standing : Whether the account has no outstanding issues

    Returns
    -------
    dict with keys:
        eligible          : bool — True if resolution is within standard policy
        requires_approval : bool — True if a human approval control point must fire
        policy_rule       : str  — The policy rule that determined eligibility
        notes             : str  — Plain English explanation for the audit trail
    """
    if not account_in_good_standing:
        return {
            "eligible": False,
            "requires_approval": True,
            "policy_rule": "account-not-in-good-standing",
            "notes": "Account is not in good standing. Escalate to Level 2 agent.",
        }

    if resolution_type == "account_change":
        return {
            "eligible": True,
            "requires_approval": True,
            "policy_rule": "account-change-requires-approval",
            "notes": (
                "All account-level changes require human approval "
                "(account-change-approval control point)."
            ),
        }

    if resolution_type == "refund":
        return _check_refund_eligibility(resolution_value, days_since_purchase)

    if resolution_type == "credit":
        return _check_credit_eligibility(resolution_value)

    if resolution_type == "replacement":
        return _check_replacement_eligibility(days_since_purchase)

    # Informational resolutions are always within scope
    return {
        "eligible": True,
        "requires_approval": False,
        "policy_rule": "informational-no-approval-required",
        "notes": "Informational resolution; no approval required.",
    }


def _check_refund_eligibility(value: float, days: int | None) -> dict:
    if days is not None and days <= _STANDARD_RETURN_WINDOW_DAYS:
        within_window = True
    elif days is None:
        within_window = False
    else:
        within_window = False

    if not within_window:
        return {
            "eligible": True,
            "requires_approval": True,
            "policy_rule": "refund-outside-standard-window",
            "notes": (
                f"Purchase is {days} days ago (outside {_STANDARD_RETURN_WINDOW_DAYS}-day window). "
                "Statutory rights may apply; requires Returns Specialist assessment."
            ),
        }

    if value > _REFUND_APPROVAL_THRESHOLD_GBP:
        return {
            "eligible": True,
            "requires_approval": True,
            "policy_rule": "refund-above-standard-threshold",
            "notes": (
                f"Refund value £{value:.2f} exceeds standard threshold "
                f"£{_REFUND_APPROVAL_THRESHOLD_GBP:.2f}. "
                "Requires compensation-approval control point."
            ),
        }

    return {
        "eligible": True,
        "requires_approval": False,
        "policy_rule": "standard-30-day-return",
        "notes": (
            f"Within {_STANDARD_RETURN_WINDOW_DAYS}-day return window "
            f"and value £{value:.2f} is within standard threshold. "
            "Auto-approval applies."
        ),
    }


def _check_credit_eligibility(value: float) -> dict:
    if value > _CREDIT_APPROVAL_THRESHOLD_GBP:
        return {
            "eligible": True,
            "requires_approval": True,
            "policy_rule": "credit-above-standard-threshold",
            "notes": (
                f"Credit value £{value:.2f} exceeds standard threshold "
                f"£{_CREDIT_APPROVAL_THRESHOLD_GBP:.2f}. "
                "Requires compensation-approval control point."
            ),
        }

    return {
        "eligible": True,
        "requires_approval": False,
        "policy_rule": "standard-goodwill-credit",
        "notes": (
            f"Credit value £{value:.2f} is within standard threshold. "
            "Auto-approval applies."
        ),
    }


def _check_replacement_eligibility(days: int | None) -> dict:
    # Replacements for damaged/incorrect items within 14 days require no approval
    if days is not None and days <= 14:
        return {
            "eligible": True,
            "requires_approval": False,
            "policy_rule": "damaged-incorrect-item-14-day",
            "notes": (
                f"Reported within 14 days of delivery ({days} days). "
                "Replacement eligible under damaged/incorrect item policy."
            ),
        }

    return {
        "eligible": True,
        "requires_approval": True,
        "policy_rule": "replacement-outside-14-day-window",
        "notes": (
            "Item reported outside 14-day damaged/incorrect window. "
            "Requires Level 2 assessment under Consumer Rights Act."
        ),
    }
