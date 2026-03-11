"""
lookup_order.py — Customer Support Agent (Digital Music Store)
==============================================================
Queries the Chinook music database to look up songs, artists, albums,
and purchase history for customer service lookup requests.

Used by activity: lookup-music

The Chinook database simulates a digital music store with tables for:
  - Artist, Album, Track — music catalog
  - Customer, Invoice, InvoiceLine — purchase history

When env="test" is passed, the function returns deterministic mock data
without touching the database, matching the LangSmith evaluate-complex-agent
test configuration pattern (config={"env": "test"}).

Usage
-----
    from scripts.lookup_order import lookup_music, lookup_purchase_history

    # Look up tracks by artist name
    result = lookup_music(query="Jimi Hendrix", search_type="artist", env="test")
    # {
    #   "tracks": [...],
    #   "count": 2,
    #   "search_type": "artist",
    #   "query": "Jimi Hendrix",
    #   "mock": True
    # }

    # Look up a customer's purchase history
    history = lookup_purchase_history(customer_name="Claude Shannon", env="test")
    # {"invoices": [...], "customer_id": 42, "count": 1, "mock": True}
"""

import sqlite3
from pathlib import Path
from typing import Literal

SearchType = Literal["artist", "album", "track", "all"]

# Default database path — override db_path argument for custom locations
_DEFAULT_DB_PATH = Path(__file__).parent.parent / "resources" / "chinook.db"


def lookup_music(
    query: str,
    search_type: SearchType = "all",
    db_path: str | Path | None = None,
    env: str = "production",
) -> dict:
    """
    Search the Chinook music catalog for tracks, albums, or artists.

    Parameters
    ----------
    query       : Search term (e.g. artist name, album title, or track title)
    search_type : Scope — "artist", "album", "track", or "all"
    db_path     : Path to the Chinook SQLite database (defaults to bundled DB)
    env         : "test" returns mock data without DB access; "production" queries live DB

    Returns
    -------
    dict with keys:
        tracks      : list of matching track records (ArtistName, AlbumTitle,
                      TrackName, Milliseconds, UnitPrice)
        count       : int — number of results found
        search_type : str — the search scope used
        query       : str — the original search term
        mock        : bool — present and True when env="test"
    """
    if env == "test":
        return _mock_lookup(query, search_type)

    resolved_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
    if not resolved_path.exists():
        return {
            "tracks": [],
            "count": 0,
            "search_type": search_type,
            "query": query,
            "error": f"Database not found at {resolved_path}",
        }

    with sqlite3.connect(resolved_path) as conn:
        conn.row_factory = sqlite3.Row
        results = _run_catalog_query(conn, query, search_type)

    return {
        "tracks": [dict(r) for r in results],
        "count": len(results),
        "search_type": search_type,
        "query": query,
    }


def lookup_purchase_history(
    customer_name: str,
    db_path: str | Path | None = None,
    env: str = "production",
) -> dict:
    """
    Retrieve a customer's purchase history from the Chinook database.

    Used during the refund path to locate the invoice the customer wants
    refunded before the process-refund activity is invoked.

    Parameters
    ----------
    customer_name : Full name of the customer ("First Last")
    db_path       : Path to the Chinook SQLite database
    env           : "test" returns mock data without DB access

    Returns
    -------
    dict with keys:
        invoices    : list of invoice records with per-track line items
        customer_id : int — Chinook CustomerId (None if customer not found)
        count       : int — number of invoices found
        mock        : bool — present and True when env="test"
    """
    if env == "test":
        return _mock_purchase_history(customer_name)

    resolved_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
    if not resolved_path.exists():
        return {
            "invoices": [],
            "customer_id": None,
            "count": 0,
            "error": f"Database not found at {resolved_path}",
        }

    parts = customer_name.strip().split(maxsplit=1)
    first = parts[0] if parts else ""
    last = parts[1] if len(parts) > 1 else ""

    with sqlite3.connect(resolved_path) as conn:
        conn.row_factory = sqlite3.Row

        customer = conn.execute(
            "SELECT CustomerId FROM Customer WHERE FirstName=? AND LastName=?",
            (first, last),
        ).fetchone()

        if not customer:
            return {"invoices": [], "customer_id": None, "count": 0}

        customer_id = customer["CustomerId"]
        invoices = conn.execute(
            """
            SELECT i.InvoiceId, i.InvoiceDate, i.Total,
                   il.TrackId, t.Name AS TrackName,
                   al.Title AS AlbumTitle, ar.Name AS ArtistName
              FROM Invoice i
              JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId
              JOIN Track t ON t.TrackId = il.TrackId
              JOIN Album al ON al.AlbumId = t.AlbumId
              JOIN Artist ar ON ar.ArtistId = al.ArtistId
             WHERE i.CustomerId = ?
             ORDER BY i.InvoiceDate DESC
            """,
            (customer_id,),
        ).fetchall()

    return {
        "invoices": [dict(r) for r in invoices],
        "customer_id": customer_id,
        "count": len(invoices),
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _run_catalog_query(
    conn: sqlite3.Connection, query: str, search_type: SearchType
) -> list:
    param = f"%{query}%"
    base_select = """
        SELECT ar.Name AS ArtistName, al.Title AS AlbumTitle,
               t.Name AS TrackName, t.Milliseconds, t.UnitPrice
          FROM Track t
          JOIN Album al ON al.AlbumId = t.AlbumId
          JOIN Artist ar ON ar.ArtistId = al.ArtistId
    """

    if search_type == "artist":
        return conn.execute(
            base_select + " WHERE ar.Name LIKE ? ORDER BY ar.Name, al.Title, t.Name",
            (param,),
        ).fetchall()

    if search_type == "album":
        return conn.execute(
            base_select + " WHERE al.Title LIKE ? ORDER BY al.Title, t.Name",
            (param,),
        ).fetchall()

    if search_type == "track":
        return conn.execute(
            base_select + " WHERE t.Name LIKE ? ORDER BY t.Name",
            (param,),
        ).fetchall()

    # search_type == "all"
    return conn.execute(
        base_select + " WHERE ar.Name LIKE ? OR al.Title LIKE ? OR t.Name LIKE ?"
        " ORDER BY ar.Name, al.Title, t.Name",
        (param, param, param),
    ).fetchall()


def _mock_lookup(query: str, search_type: SearchType) -> dict:
    """Return deterministic mock catalog data for test environments."""
    mock_tracks = [
        {
            "ArtistName": f"{query}",
            "AlbumTitle": "Mock Album Vol. 1",
            "TrackName": "Mock Track 1",
            "Milliseconds": 210000,
            "UnitPrice": 0.99,
        },
        {
            "ArtistName": f"{query}",
            "AlbumTitle": "Mock Album Vol. 1",
            "TrackName": "Mock Track 2",
            "Milliseconds": 195000,
            "UnitPrice": 0.99,
        },
    ]
    return {
        "tracks": mock_tracks,
        "count": len(mock_tracks),
        "search_type": search_type,
        "query": query,
        "mock": True,
    }


def _mock_purchase_history(customer_name: str) -> dict:
    """Return deterministic mock purchase history for test environments."""
    return {
        "invoices": [
            {
                "InvoiceId": 1001,
                "InvoiceDate": "2026-02-10",
                "Total": 1.98,
                "TrackId": 501,
                "TrackName": "Mock Track 1",
                "AlbumTitle": "Mock Album Vol. 1",
                "ArtistName": "Mock Artist",
            }
        ],
        "customer_id": 42,
        "count": 1,
        "mock": True,
    }
