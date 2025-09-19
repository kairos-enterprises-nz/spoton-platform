from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SyncResult:
    success: bool
    message: str = ""
    external_id: str | None = None


class AccountingProvider(Protocol):
    def push_invoice(self, invoice) -> SyncResult: ...
    def fetch_payment_status(self, invoice) -> SyncResult: ...


class XeroSandboxProvider:
    def push_invoice(self, invoice) -> SyncResult:
        return SyncResult(success=True, message='Stub push OK', external_id=f"XERO-{invoice.invoice_number}")

    def fetch_payment_status(self, invoice) -> SyncResult:
        return SyncResult(success=True, message='Stub status unpaid')


class MYOBSandboxProvider:
    def push_invoice(self, invoice) -> SyncResult:
        return SyncResult(success=True, message='Stub push OK', external_id=f"MYOB-{invoice.invoice_number}")

    def fetch_payment_status(self, invoice) -> SyncResult:
        return SyncResult(success=True, message='Stub status unpaid')


class QuickBooksSandboxProvider:
    def push_invoice(self, invoice) -> SyncResult:
        return SyncResult(success=True, message='Stub push OK', external_id=f"QB-{invoice.invoice_number}")

    def fetch_payment_status(self, invoice) -> SyncResult:
        return SyncResult(success=True, message='Stub status unpaid')

