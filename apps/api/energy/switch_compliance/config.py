# -*- coding: utf-8 -*-
"""
================================================================================
Compliance Configuration for the Automated Electricity Switching System
================================================================================

Version: 1.0
Author: Lead Systems Architect

Purpose:
This module provides a single, authoritative source for all timeframes,
breach conditions, and business day logic governing the automated electricity
switching workflows. It directly implements the rules outlined in the
Electricity Authority Participation Code (Schedule 11.3) and the
Registry Functional Specification (e.g., PR-040).

This configuration MUST be imported by all relevant Airflow DAGs and utility
functions to ensure consistent and compliant process execution. It should be
treated as a static asset, with changes managed under strict version control.
"""

from datetime import time

# =============================================================================
# 1. BUSINESS CALENDAR & WORKING HOURS DEFINITION
# =============================================================================

# This list must be updated annually as part of operational procedure.
# It should contain all national public holidays for New Zealand as 'YYYY-MM-DD' strings.
# This list is used by the business day calculation utility.
PUBLIC_HOLIDAYS = [
    # --- 2024 Holidays (Example) ---
    "2024-01-01",  # New Year's Day
    "2024-01-02",  # Day after New Year's Day
    "2024-02-06",  # Waitangi Day
    "2024-03-29",  # Good Friday
    "2024-04-01",  # Easter Monday
    "2024-04-25",  # ANZAC Day
    "2024-06-03",  # King's Birthday
    "2024-06-28",  # Matariki
    "2024-10-28",  # Labour Day
    "2024-12-25",  # Christmas Day
    "2024-12-26",  # Boxing Day
    # --- 2025 Holidays (Placeholder) ---
    # "2025-01-01", "2025-01-02", ...
]

# Defines the official working hours for message receipt as per the Code.
# Any message received outside these hours is normalized to the start of the
# next appropriate business day.
WORKING_HOURS = {
    'start': time(7, 30),
    'end': time(19, 30),
}

# =============================================================================
# 2. SWITCHING TIMEFRAME AND BREACH CONFIGURATION
# =============================================================================
# This dictionary codifies the rules from the Registry Functional Specification.
# The structure is: RULE_SET -> SWITCH_TYPE -> {rule_details}.

SWITCHING_TIMEFRAMES = {
    # -------------------------------------------------------------------------
    # Rule Set: NT_SUBMISSION
    # The Gaining Trader must initiate the switch in a timely manner. This is a
    # critical first step and a primary compliance metric.
    # Trigger: Contract status becomes 'READY'.
    # -------------------------------------------------------------------------
    'NT_SUBMISSION': {
        'ALL': {
            'due_business_days': 2,
            'breaching_participant': 'GAINING_TRADER',
            'trigger_event': 'CONTRACT_READY',
            'response_message': 'NT',
            'description': 'Gaining Trader: NT must be submitted to the Registry within 2 business days of the customer arrangement becoming effective.'
        }
    },

    # -------------------------------------------------------------------------
    # Rule Set: AN_DELIVERY (Acknowledgement of an NT)
    # The Losing Trader must acknowledge receipt of the NT.
    # Trigger: Inbound NT is received from the Registry.
    # -------------------------------------------------------------------------
    'AN_DELIVERY': {
        'MI': {  # Move-In switch
            'due_business_days': 5,
            'breaching_participant': 'LOSING_TRADER',
            'trigger_message': 'NT',
            'response_message': 'AN',
            'description': 'Losing Trader: AN (Acknowledgement) must be sent within 5 business days of NT receipt for a Move-In switch.'
        },
        'TR': {  # Standard switch
            'due_business_days': 3,
            'breaching_participant': 'LOSING_TRADER',
            'trigger_message': 'NT',
            'response_message': 'AN',
            'description': 'Losing Trader: AN (Acknowledgement) must be sent within 3 business days of NT receipt for a Standard switch.'
        },
        'HH': {  # Half-Hour switch
            'due_business_days': 3,
            'breaching_participant': 'LOSING_TRADER',
            'trigger_message': 'NT',
            'response_message': 'AN',
            'description': 'Losing Trader: AN (Acknowledgement) must be sent within 3 business days of NT receipt for a Half-Hour switch.'
        }
    },

    # -------------------------------------------------------------------------
    # Rule Set: CS_DELIVERY (Completion of a Switch)
    # The responsible party must send the final meter reading.
    # Trigger: AN is received (or NT, if no AN is sent). Timer is relative to the
    # proposed or actual transfer date.
    # -------------------------------------------------------------------------
    'CS_DELIVERY': {
        'TR': {
            'due_business_days': 5,
            'breaching_participant': 'LOSING_TRADER',
            'trigger_message': 'AN',
            'response_message': 'CS',
            'description': 'Losing Trader: CS (Complete Switch) arrival must be no more than 5 business days after the Actual Transfer Date.'
        },
        'HH': {
            'due_business_days': 3,
            'breaching_participant': 'GAINING_TRADER',
            'trigger_message': 'AN',
            'response_message': 'CS',
            'description': 'Gaining Trader: CS (Complete Switch) must be sent within 3 business days of receiving the AN.'
        }
    },

    # -------------------------------------------------------------------------
    # Rule Set: RR_DELIVERY (Gaining Trader disputes a reading)
    # This is an exception flow that happens post-completion.
    # Trigger: Original CS message completion date.
    # -------------------------------------------------------------------------
    'RR_DELIVERY': {
        'ALL': {
            'due_calendar_months': 4,
            'breaching_participant': 'GAINING_TRADER',
            'trigger_message': 'CS',
            'response_message': 'RR',
            'description': 'Gaining Trader: RR (Replacement Reading) must be sent within 4 calendar months of the original CS Actual Transfer Date.'
        }
    },

    # -------------------------------------------------------------------------
    # Rule Set: AC_DELIVERY (Losing Trader responds to an RR)
    # The response to a reading correction request.
    # Trigger: Inbound RR is received.
    # -------------------------------------------------------------------------
    'AC_DELIVERY': {
        'ALL': {
            'due_business_days': 5,
            'breaching_participant': 'LOSING_TRADER',
            'trigger_message': 'RR',
            'response_message': 'AC',
            'description': 'Losing Trader: AC (Acknowledge Change) must be sent within 5 business days of RR receipt.'
        }
    },

    # -------------------------------------------------------------------------
    # Rule Set: AW_DELIVERY (Responding to a withdrawal request)
    # Trigger: Inbound NW is received.
    # -------------------------------------------------------------------------
    'AW_DELIVERY': {
        'ALL': {
            'due_business_days': 5,
            'breaching_participant': 'RESPONDING_TRADER', # Could be us or them
            'trigger_message': 'NW',
            'response_message': 'AW',
            'description': 'A response (AW) to a withdrawal notice (NW) must be sent within 5 business days of receipt.'
        }
    },

    # -------------------------------------------------------------------------
    # Rule Set: WITHDRAWAL_CYCLE_RESOLUTION
    # Ensures a withdrawal process we initiated is eventually resolved. This is an
    # internal process check to prevent stuck workflows.
    # Trigger: Outbound NW is sent.
    # -------------------------------------------------------------------------
    'WITHDRAWAL_CYCLE_RESOLUTION': {
        'ALL': {
            'due_business_days': 10,
            'breaching_participant': 'RESPONDING_TRADER',
            'trigger_message': 'NW',
            'response_message': 'AW',
            'description': 'An acknowledgement (AW) was not received from the responding trader within 10 business days of the initial withdrawal request (NW).'
        }
    }
} 