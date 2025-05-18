from datetime import datetime
from decimal import Decimal

from app import db
from app.models import Transaction, TransactionType, TransactionCategory

class TransactionService:
    """Service for handling transaction business logic"""
    
    def create_transaction(self, user_id, **data):
        """
        Create a new transaction
        
        Args:
            user_id (int): ID of the user creating the transaction
            **data: Transaction data
                - date (str): Transaction date in YYYY-MM-DD format
                - amount (float): Transaction amount
                - type (str): Transaction type (income/expense/transfer)
                - category (str): Transaction category
                - description (str, optional): Transaction description
                - reference (str, optional): Reference number
                - is_reconciled (bool, optional): Whether transaction is reconciled
                - receipt_url (str, optional): URL to receipt
                - project_id (int, optional): Associated project ID
                - invoice_id (int, optional): Associated invoice ID
                
        Returns:
            Transaction: The created transaction
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        required_fields = ['date', 'amount', 'type', 'category']
        for field in required_fields:
            if field not in data:
                raise ValueError(f'Missing required field: {field}')
        
        try:
            # Convert and validate transaction type
            transaction_type = TransactionType(data['type'])
            
            # Convert and validate category
            category = TransactionCategory(data['category'])
            
            # Convert date string to date object
            date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            # Create transaction
            transaction = Transaction(
                date=date,
                amount=data['amount'],
                type=transaction_type,
                category=category,
                description=data.get('description'),
                reference=data.get('reference'),
                is_reconciled=bool(data.get('is_reconciled', False)),
                receipt_url=data.get('receipt_url'),
                project_id=data.get('project_id'),
                invoice_id=data.get('invoice_id'),
                user_id=user_id
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return transaction
            
        except ValueError as e:
            db.session.rollback()
            raise ValueError(f'Invalid data: {str(e)}')
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Failed to create transaction: {str(e)}')
    
    def update_transaction(self, transaction, **data):
        """
        Update an existing transaction
        
        Args:
            transaction (Transaction): Transaction to update
            **data: Fields to update
                - date (str, optional): Transaction date in YYYY-MM-DD format
                - amount (float, optional): Transaction amount
                - type (str, optional): Transaction type (income/expense/transfer)
                - category (str, optional): Transaction category
                - description (str, optional): Transaction description
                - reference (str, optional): Reference number
                - is_reconciled (bool, optional): Whether transaction is reconciled
                - receipt_url (str, optional): URL to receipt
                - project_id (int, optional): Associated project ID
                - invoice_id (int, optional): Associated invoice ID
                
        Returns:
            Transaction: The updated transaction
            
        Raises:
            ValueError: If provided data is invalid
        """
        try:
            if 'date' in data:
                transaction.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                
            if 'amount' in data:
                transaction.amount = data['amount']
                
            if 'type' in data:
                transaction.type = TransactionType(data['type'])
                
            if 'category' in data:
                transaction.category = TransactionCategory(data['category'])
                
            # Update optional fields if provided
            optional_fields = [
                'description', 'reference', 'is_reconciled', 
                'receipt_url', 'project_id', 'invoice_id'
            ]
            
            for field in optional_fields:
                if field in data:
                    setattr(transaction, field, data[field])
            
            db.session.commit()
            return transaction
            
        except ValueError as e:
            db.session.rollback()
            raise ValueError(f'Invalid data: {str(e)}')
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Failed to update transaction: {str(e)}')
    
    def delete_transaction(self, transaction_id, user_id):
        """
        Delete a transaction
        
        Args:
            transaction_id (int): ID of the transaction to delete
            user_id (int): ID of the user making the request
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            ValueError: If transaction not found or not owned by user
        """
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=user_id
        ).first()
        
        if not transaction:
            raise ValueError('Transaction not found or access denied')
        
        try:
            db.session.delete(transaction)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Failed to delete transaction: {str(e)}')
    
    def get_transaction_summary(self, user_id, start_date=None, end_date=None):
        """
        Get transaction summary for a user within a date range
        
        Args:
            user_id (int): ID of the user
            start_date (date, optional): Start date of the period
            end_date (date, optional): End date of the period
            
        Returns:
            dict: Summary of transactions
        """
        query = Transaction.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        # Group by type and category
        results = query.with_entities(
            Transaction.type,
            Transaction.category,
            db.func.sum(Transaction.amount).label('total_amount')
        ).group_by(Transaction.type, Transaction.category).all()
        
        # Format results
        summary = {
            'total_income': Decimal('0'),
            'total_expenses': Decimal('0'),
            'by_category': {},
            'by_type': {}
        }
        
        for type_, category, amount in results:
            amount = amount or Decimal('0')
            
            # Update type totals
            if type_ not in summary['by_type']:
                summary['by_type'][type_] = Decimal('0')
            summary['by_type'][type_] += amount
            
            # Update category totals
            if category not in summary['by_category']:
                summary['by_category'][category] = Decimal('0')
            summary['by_category'][category] += amount
            
            # Update overall totals
            if type_ == TransactionType.INCOME:
                summary['total_income'] += amount
            else:
                summary['total_expenses'] += amount
        
        summary['net_income'] = summary['total_income'] - summary['total_expenses']
        
        # Convert Decimal to float for JSON serialization
        for key in ['total_income', 'total_expenses', 'net_income']:
            summary[key] = float(summary[key])
            
        for key in summary['by_type']:
            summary['by_type'][key] = float(summary['by_type'][key])
            
        for key in summary['by_category']:
            summary['by_category'][key] = float(summary['by_category'][key])
        
        return summary
