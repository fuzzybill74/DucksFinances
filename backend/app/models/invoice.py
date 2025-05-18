from datetime import datetime
from enum import Enum
from decimal import Decimal
from app import db

class InvoiceStatus(str, Enum):
    DRAFT = 'draft'
    SENT = 'sent'
    VIEWED = 'viewed'
    PARTIALLY_PAID = 'partially_paid'
    PAID = 'paid'
    OVERDUE = 'overdue'
    VOID = 'void'
    UNCOLLECTIBLE = 'uncollectible'

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1.0)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Foreign Keys
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'quantity': float(self.quantity) if self.quantity is not None else None,
            'unit_price': float(self.unit_price) if self.unit_price is not None else None,
            'tax_rate': float(self.tax_rate) if self.tax_rate is not None else None,
            'amount': float(self.amount) if self.amount is not None else None,
            'invoice_id': self.invoice_id
        }
    
    def calculate_amount(self):
        return Decimal(str(self.quantity)) * self.unit_price * (1 + self.tax_rate / 100)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    notes = db.Column(db.Text)
    terms = db.Column(db.Text)
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00)
    subtotal = db.Column(db.Numeric(12, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(12, 2), default=0.00)
    total = db.Column(db.Numeric(12, 2), default=0.00)
    amount_paid = db.Column(db.Numeric(12, 2), default=0.00)
    amount_due = db.Column(db.Numeric(12, 2), default=0.00)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    
    # Relationships
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='invoice', lazy=True)
    
    def calculate_totals(self):
        self.subtotal = sum(item.amount for item in self.items)
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount
        self.amount_due = self.total - self.amount_paid
        
        # Update status based on payments
        if self.amount_due <= 0:
            self.status = InvoiceStatus.PAID
        elif self.amount_paid > 0:
            self.status = InvoiceStatus.PARTIALLY_PAID
            
        return self
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status.value,
            'notes': self.notes,
            'terms': self.terms,
            'tax_rate': float(self.tax_rate) if self.tax_rate is not None else None,
            'subtotal': float(self.subtotal) if self.subtotal is not None else None,
            'tax_amount': float(self.tax_amount) if self.tax_amount is not None else None,
            'total': float(self.total) if self.total is not None else None,
            'amount_paid': float(self.amount_paid) if self.amount_paid is not None else None,
            'amount_due': float(self.amount_due) if self.amount_due is not None else None,
            'currency': self.currency,
            'user_id': self.user_id,
            'client_id': self.client_id,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items]
        }
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}: {self.total} {self.currency}>'
