"""
refund_item.py — Customer Support Agent (Digital Music Store)
=============================================================
Processes customer refund requests by removing the corresponding Invoice
and InvoiceLine records from the Chinook database.

Used by activity: process-refund

Refunds are implemented as a DELETE of the Invoice and its associated
InvoiceLine rows. This operation is intentionally destructive — the
`refund-approval` control point (needs_approval classification) MUST be
cleared by a human reviewer before this function is called.

When env="test" is passed, the deletion is fully mocked: the function
returns a success response without modifying any database records. This
matches the LangSmith evaluate-complex-agent test configuration pattern:
    config={"env": "test"}

Usage
-----
    from scripts.refund_item import process_refund

    # Test mode — no DB changes
    result = process_refund(invoice_id=42, customer_id=7, env="test")
    # {
    #   "success": True,
    #   "invoice_id": 42,
    #   "rows_deleted": 0,
    #   "mock": True
    # }

    # Production mode — deletes Invoice and InvoiceLine records
    result = process_refund(invoice_id=42, customer_id=7, env="production")
    # {
    #   "success": True,
    #   "invoice_id": 42,
    #   "rows_deleted": 3,   # number of InvoiceLine rows removed
    #   "mock": False
    # }
"""

import sqlite3
from pathlib import Path

_DEFAULT_DB_PATH = Path(__file__).parent.parent / "resources" / "chinook.db"


def process_refund(
    invoice_id: int,
    customer_id: int,
    db_path: str | Path | None = None,
    env: str = "production",
) -> dict:
    """
    Process a refund by removing the invoice record from the Chinook database.

    The `refund-approval` control point (needs_approval) must be explicitly
    cleared by a human reviewer before this function is invoked. Never call
    this function without a cleared refund-approval control point.

    Parameters
    ----------
    invoice_id  : The Chinook InvoiceId to be deleted
    customer_id : The Chinook CustomerId; must match the invoice owner
    db_path     : Path to the Chinook SQLite database (defaults to bundled DB)
    env         : "test" mocks the deletion; "production" performs the actual DELETE

    Returns
    -------
    dict with keys:
        success      : bool — True if refund was processed (or mocked) successfully
        invoice_id   : int  — The invoice that was (or would be) deleted
        rows_deleted : int  — Number of InvoiceLine rows removed (0 in test mode)
        mock         : bool — True when env="test"
        error        : str  — Present only if an error occurred
    """
    if env == "test":
        return {
            "success": True,
            "invoice_id": invoice_id,
            "rows_deleted": 0,
            "mock": True,
        }

    resolved_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
    if not resolved_path.exists():
        return {
            "success": False,
            "invoice_id": invoice_id,
            "rows_deleted": 0,
            "mock": False,
            "error": f"Database not found at {resolved_path}",
        }

    try:
        with sqlite3.connect(resolved_path) as conn:
            # Verify the invoice exists and belongs to this customer
            owner = conn.execute(
                "SELECT CustomerId FROM Invoice WHERE InvoiceId=?",
                (invoice_id,),
            ).fetchone()

            if not owner:
                return {
                    "success": False,
                    "invoice_id": invoice_id,
                    "rows_deleted": 0,
                    "mock": False,
                    "error": f"Invoice {invoice_id} not found.",
                }

            if owner[0] != customer_id:
                return {
                    "success": False,
                    "invoice_id": invoice_id,
                    "rows_deleted": 0,
                    "mock": False,
                    "error": (
                        f"Invoice {invoice_id} does not belong to "
                        f"customer {customer_id}. Refund denied."
                    ),
                }

            # Delete line items first (foreign key constraint)
            line_result = conn.execute(
                "DELETE FROM InvoiceLine WHERE InvoiceId=?", (invoice_id,)
            )
            rows_deleted = line_result.rowcount

            conn.execute("DELETE FROM Invoice WHERE InvoiceId=?", (invoice_id,))
            conn.commit()

        return {
            "success": True,
            "invoice_id": invoice_id,
            "rows_deleted": rows_deleted,
            "mock": False,
        }

    except sqlite3.Error as exc:
        return {
            "success": False,
            "invoice_id": invoice_id,
            "rows_deleted": 0,
            "mock": False,
            "error": str(exc),
        }
