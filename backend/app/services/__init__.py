# This file makes the services directory a Python package
from .auth_service import AuthService
from .transaction_service import TransactionService
from .invoice_service import InvoiceService

# Initialize service instances
auth_service = AuthService()
transaction_service = TransactionService()
invoice_service = InvoiceService()
