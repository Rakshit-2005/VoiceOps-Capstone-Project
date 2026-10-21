"""Tool calling, caller identity verification, and business date logic for ZentroMart.

Wraps tools/tools.py with verification attempt tracking, business-day timeline math,
and structured handover ticket generation.
"""

import os
import re
import sys
from datetime import date, timedelta
from typing import Dict, Any, Optional, Tuple

from src.config import TOOLS_DIR, DATA_DIR, REFERENCE_DATE, HOLIDAYS, is_business_day, add_business_days, parse_date_str

# Import the provided mock tools
sys.path.insert(0, TOOLS_DIR)
try:
    from tools import lookup_order as _raw_lookup_order, create_ticket as _raw_create_ticket
except ImportError:
    # Fallback to local package import if executed from project root
    from tools.tools import lookup_order as _raw_lookup_order, create_ticket as _raw_create_ticket


class ToolsHandler:
    def __init__(self):
        self.verified_sessions: Dict[str, Dict[str, Any]] = {}
        self.retry_counts: Dict[str, int] = {}

    def extract_order_id(self, text: str) -> Optional[str]:
        """Extract an 8-digit order ID from text (with or without spaces/hyphens)."""
        # Matches patterns like '8978 2837', '8978-2837', '89782837'
        match = re.search(r'\b(\d{4})[\s\-]?(\d{4})\b', text)
        if match:
            return match.group(1) + match.group(2)
        # Any 8 consecutive digits
        match8 = re.search(r'\b\d{8}\b', text)
        if match8:
            return match8.group(0)
        return None

    def extract_verification_code(self, text: str) -> Optional[str]:
        """Extract a 4-digit phone suffix or 6-digit pincode from user input."""
        # 6-digit pincode
        pin_match = re.search(r'\b\d{6}\b', text)
        if pin_match:
            return pin_match.group(0)
        # 4-digit phone suffix
        digits4 = re.findall(r'\b\d{4}\b', text)
        if digits4:
            return digits4[-1]
        return None

    def lookup(self, order_id: str, verification_val: Optional[str] = None) -> Dict[str, Any]:
        """Execute lookup_order with safety gating and retry enforcement."""
        clean_oid = ''.join(ch for ch in str(order_id) if '0' <= ch <= '9')
        
        # Check if already verified in this session
        if clean_oid in self.verified_sessions:
            cached = self.verified_sessions[clean_oid]
            return {**cached, "already_verified": True}
            
        retries = self.retry_counts.get(clean_oid, 0)
        if retries >= 2 and verification_val is not None:
            return {
                "verified": False,
                "verification_required": True,
                "max_retries_exceeded": True,
                "message": "Maximum verification attempts exceeded. Please connect with human support."
            }

        res = _raw_lookup_order(order_id=clean_oid, verification_value=verification_val)
        
        if res.get("verified"):
            self.verified_sessions[clean_oid] = res
            return res
        elif verification_val is not None:
            self.retry_counts[clean_oid] = retries + 1
            res["retries_left"] = max(0, 1 - self.retry_counts[clean_oid])
            
        return res

    def create_support_ticket(self, summary: str, order_id: Optional[str] = None,
                              reason: Optional[str] = None, intent: Optional[str] = None) -> Dict[str, Any]:
        """Create ticket for human handover. Requires descriptive summary."""
        if not summary or len(summary.strip()) < 20:
            summary = f"Customer issue for order {order_id or 'general'}: {reason or 'escalation'} - {summary or 'human review required'}"
            
        res = _raw_create_ticket(
            summary=summary,
            order_id=order_id,
            reason=reason,
            intent=intent
        )
        return res

    @staticmethod
    def calculate_return_deadline(delivery_date_str: str, window_days: int) -> Tuple[date, bool]:
        """Calculate return deadline using calendar days from delivery date."""
        deliv = parse_date_str(delivery_date_str)
        deadline = deliv + timedelta(days=window_days)
        is_eligible = REFERENCE_DATE <= deadline
        return deadline, is_eligible

    @staticmethod
    def calculate_refund_window(start_date_str: str, min_days: int, max_days: int) -> Tuple[date, date]:
        """Calculate refund expected date range using business days (Mon-Sat minus holidays)."""
        st = parse_date_str(start_date_str)
        min_date = add_business_days(st, min_days)
        max_date = add_business_days(st, max_days)
        return min_date, max_date
