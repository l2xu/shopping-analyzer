"""API client module for shopping analyzer."""

from .lidl_client import get_tickets_page, get_receipt_details_and_html

__all__ = [
    "get_tickets_page",
    "get_receipt_details_and_html",
]
