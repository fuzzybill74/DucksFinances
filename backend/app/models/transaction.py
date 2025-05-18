from datetime import datetime
from enum import Enum
from app import db

class TransactionType(str, Enum):
    INCOME = 'income'
    EXPENSE = 'expense'
    TRANSFER = 'transfer'

class TransactionCategory(str, Enum):
    # Income categories
    SERVICE = 'service'
    PRODUCT_SALE = 'product_sale'
    INTEREST = 'interest'
    REFUND = 'refund'
    OTHER_INCOME = 'other_income'
    
    # Expense categories
    OFFICE_SUPPLIES = 'office_supplies'
    RENT = 'rent'
    UTILITIES = 'utilities'
    SALARY = 'salary'
    CONTRACTOR = 'contractor'
    SOFTWARE = 'software'
    HARDWARE = 'hardware'
    TRAVEL = 'travel'
    MEALS = 'meals'
    MARKETING = 'marketing'
    PROFESSIONAL_SERVICES = 'professional_services'
    INSURANCE = 'insurance'
    TAXES = 'taxes'
    OTHER_EXPENSE = 'other_expense'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    reference = db.Column(db.String(100))
    is_reconciled = db.Column(db.Boolean, default=False)
    receipt_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Enums
    type = db.Column(db.Enum(TransactionType), nullable=False)
    category = db.Column(db.Enum(TransactionCategory), nullable=False)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'amount': float(self.amount) if self.amount is not None else None,
            'description': self.description,
            'reference': self.reference,
            'type': self.type.value,
            'category': self.category.value,
            'is_reconciled': self.is_reconciled,
            'receipt_url': self.receipt_url,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'invoice_id': self.invoice_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Transaction {self.id}: {self.amount} {self.type} for {self.description}>'
