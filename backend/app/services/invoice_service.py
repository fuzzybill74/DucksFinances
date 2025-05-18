from datetime import datetime, date
from decimal import Decimal
import re

from app import db
from app.models import Invoice, InvoiceStatus, InvoiceItem, Transaction, TransactionType

class InvoiceService:
    """Service for handling invoice business logic"""
    
    def _generate_invoice_number(self, user_id):
        """
        Generate a unique invoice number
        
        Format: INV-{year}{month}-{sequence}
        
        Args:
            user_id (int): ID of the user
            
        Returns:
            str: Generated invoice number
        """
        # Get the latest invoice for this user
        latest_invoice = Invoice.query.filter_by(user_id=user_id)\
                                    .order_by(Invoice.id.desc())\
                                    .first()
        
        current_year = date.today().year
        current_month = date.today().month
        
        if latest_invoice and latest_invoice.invoice_number:
            # Extract sequence number from the latest invoice
            match = re.match(r'INV-(\d{4})(\d{2})-(\d+)', latest_invoice.invoice_number)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                sequence = int(match.group(3))
                
                if year == current_year and month == current_month:
                    # Increment sequence for the same month
                    sequence += 1
                else:
                    # Start new sequence for new month
                    sequence = 1
            else:
                sequence = 1
        else:
            sequence = 1
        
        return f"INV-{current_year}{current_month:02d}-{sequence:04d}"
    
    def create_invoice(self, user_id, **data):
        """
        Create a new invoice
        
        Args:
            user_id (int): ID of the user creating the invoice
            **data: Invoice data
                - client_id (int): ID of the client
                - project_id (int, optional): ID of the associated project
                - issue_date (str): Invoice issue date (YYYY-MM-DD)
                - due_date (str): Invoice due date (YYYY-MM-DD)
                - currency (str, optional): Currency code (default: 'USD')
                - tax_rate (float, optional): Tax rate percentage
                - notes (str, optional): Notes for the client
                - terms (str, optional): Payment terms
                - items (list): List of invoice items
                    - description (str): Item description
                    - quantity (float): Item quantity
                    - unit_price (float): Price per unit
                    - tax_rate (float, optional): Tax rate for this item
                
        Returns:
            Invoice: The created invoice
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        required_fields = ['client_id', 'issue_date', 'due_date', 'items']
        for field in required_fields:
            if field not in data:
                raise ValueError(f'Missing required field: {field}')
        
        if not isinstance(data.get('items'), list) or len(data['items']) == 0:
            raise ValueError('At least one invoice item is required')
        
        try:
            # Convert dates
            issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            
            if due_date < issue_date:
                raise ValueError('Due date cannot be before issue date')
            
            # Create invoice
            invoice = Invoice(
                invoice_number=self._generate_invoice_number(user_id),
                issue_date=issue_date,
                due_date=due_date,
                status=InvoiceStatus.DRAFT,
                notes=data.get('notes'),
                terms=data.get('terms'),
                tax_rate=Decimal(str(data.get('tax_rate', 0))),
                currency=data.get('currency', 'USD'),
                client_id=data['client_id'],
                project_id=data.get('project_id'),
                user_id=user_id
            )
            
            # Add invoice items
            for item_data in data['items']:
                if not all(k in item_data for k in ['description', 'quantity', 'unit_price']):
                    raise ValueError('Each item must have description, quantity, and unit_price')
                
                item = InvoiceItem(
                    description=item_data['description'],
                    quantity=Decimal(str(item_data['quantity'])),
                    unit_price=Decimal(str(item_data['unit_price'])),
                    tax_rate=Decimal(str(item_data.get('tax_rate', 0))),
                    invoice=invoice
                )
                
                # Calculate item amount (quantity * unit_price * (1 + tax_rate/100))
                item.amount = item.quantity * item.unit_price * (1 + item.tax_rate / 100)
                
                db.session.add(item)
            
            # Calculate invoice totals
            invoice.calculate_totals()
            
            db.session.add(invoice)
            db.session.commit()
            
            return invoice
            
        except ValueError as e:
            db.session.rollback()
            raise ValueError(f'Invalid data: {str(e)}')
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Failed to create invoice: {str(e)}')
    
    def update_invoice(self, invoice, **data):
        """
        Update an existing invoice
        
        Args:
            invoice (Invoice): Invoice to update
            **data: Fields to update
                - client_id (int, optional): ID of the client
                - project_id (int, optional): ID of the associated project
                - issue_date (str, optional): Invoice issue date (YYYY-MM-DD)
                - due_date (str, optional): Invoice due date (YYYY-MM-DD)
                - status (str, optional): Invoice status
                - currency (str, optional): Currency code
                - tax_rate (float, optional): Tax rate percentage
                - notes (str, optional): Notes for the client
                - terms (str, optional): Payment terms
                - items (list, optional): List of invoice items
                    - id (int, optional): ID of existing item (for updates)
                    - description (str): Item description
                    - quantity (float): Item quantity
                    - unit_price (float): Price per unit
                    - tax_rate (float, optional): Tax rate for this item
                
        Returns:
            Invoice: The updated invoice
            
        Raises:
            ValueError: If provided data is invalid
        """
        try:
            # Update basic fields if provided
            if 'issue_date' in data:
                invoice.issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
                
            if 'due_date' in data:
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
                if due_date < invoice.issue_date:
                    raise ValueError('Due date cannot be before issue date')
                invoice.due_date = due_date
                
            if 'status' in data:
                invoice.status = InvoiceStatus(data['status'])
                
            # Update other fields
            optional_fields = [
                'client_id', 'project_id', 'currency', 'tax_rate',
                'notes', 'terms'
            ]
            
            for field in optional_fields:
                if field in data:
                    setattr(invoice, field, data[field])
            
            # Update or create items if provided
            if 'items' in data:
                existing_items = {item.id: item for item in invoice.items}
                new_items = []
                
                for item_data in data['items']:
                    if not all(k in item_data for k in ['description', 'quantity', 'unit_price']):
                        raise ValueError('Each item must have description, quantity, and unit_price')
                    
                    item_id = item_data.get('id')
                    
                    if item_id and item_id in existing_items:
                        # Update existing item
                        item = existing_items[item_id]
                        item.description = item_data['description']
                        item.quantity = Decimal(str(item_data['quantity']))
                        item.unit_price = Decimal(str(item_data['unit_price']))
                        item.tax_rate = Decimal(str(item_data.get('tax_rate', 0)))
                        item.amount = item.quantity * item.unit_price * (1 + item.tax_rate / 100)
                        
                        # Remove from existing items to track which ones to delete
                        del existing_items[item_id]
                    else:
                        # Create new item
                        item = InvoiceItem(
                            description=item_data['description'],
                            quantity=Decimal(str(item_data['quantity'])),
                            unit_price=Decimal(str(item_data['unit_price'])),
                            tax_rate=Decimal(str(item_data.get('tax_rate', 0))),
                            invoice=invoice
                        )
                        item.amount = item.quantity * item.unit_price * (1 + item.tax_rate / 100)
                        db.session.add(item)
                    
                    new_items.append(item)
                
                # Remove items that were not in the update
                for item in existing_items.values():
                    db.session.delete(item)
                
                # Replace invoice items with updated list
                invoice.items = new_items
            
            # Recalculate totals
            invoice.calculate_totals()
            
            db.session.commit()
            return invoice
            
        except ValueError as e:
            db.session.rollback()
            raise ValueError(f'Invalid data: {str(e)}')
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Failed to update invoice: {str(e)}')
    
    def record_payment(self, invoice, amount, payment_date, payment_method=None, notes=None):
        """
        Record a payment for an invoice
        
        Args:
            invoice (Invoice): Invoice to record payment for
            amount (float): Payment amount
            payment_date (date): Date of payment
            payment_method (str, optional): Payment method
            notes (str, optional): Payment notes
            
        Returns:
            tuple: (updated_invoice, transaction)
            
        Raises:
            ValueError: If payment amount is invalid
        """
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError('Payment amount must be greater than 0')
                
            if amount > invoice.amount_due:
                raise ValueError('Payment amount cannot be greater than the amount due')
                
            # Update invoice payment
            invoice.amount_paid += amount
            invoice.calculate_totals()
            
            # Create transaction for the payment
            transaction = Transaction(
                date=payment_date,
                amount=amount,
                type=TransactionType.INCOME,
                category='service',  # Or get from settings
                description=f'Payment for invoice {invoice.invoice_number}',
                reference=f'INV-{invoice.id}',
                is_reconciled=True,
                invoice_id=invoice.id,
                project_id=invoice.project_id,
                user_id=invoice.user_id
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return invoice, transaction
            
        except ValueError as e:
            db.session.rollback()
            raise ValueError(str(e))
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Failed to record payment: {str(e)}')
    
    def send_invoice(self, invoice, send_email=True, **kwargs):
        """
        Send invoice to client
        
        Args:
            invoice (Invoice): Invoice to send
            send_email (bool): Whether to send email notification
            **kwargs: Additional options
                - email_template (str): Custom email template
                - cc (list): CC email addresses
                - bcc (list): BCC email addresses
                - subject (str): Email subject
                - message (str): Email message body
                
        Returns:
            bool: True if sent successfully
            
        Note:
            This is a placeholder for actual email sending functionality.
            Implement email sending based on your email service provider.
        """
        try:
            # Update invoice status
            if invoice.status == InvoiceStatus.DRAFT:
                invoice.status = InvoiceStatus.SENT
                db.session.commit()
            
            if send_email:
                # TODO: Implement actual email sending
                # This is just a placeholder
                client_email = invoice.client.email if invoice.client else None
                if not client_email:
                    raise ValueError('Client email not found')
                
                # Prepare email data
                email_data = {
                    'to': client_email,
                    'subject': kwargs.get('subject', f'Invoice {invoice.invoice_number} from Your Company'),
                    'template': kwargs.get('email_template', 'invoice_email.html'),
                    'context': {
                        'invoice': invoice,
                        'company_name': 'Your Company',  # Get from settings
                        'message': kwargs.get('message', 'Please find attached your invoice.')
                    },
                    'cc': kwargs.get('cc', []),
                    'bcc': kwargs.get('bcc', [])
                }
                
                # TODO: Send email using your email service
                # Example: send_email(**email_data)
                
                # For now, just log that we would send an email
                print(f"Would send email to {client_email} with subject: {email_data['subject']}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Failed to send invoice: {str(e)}')
