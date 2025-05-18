from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import desc, or_

from app import db
from app.models import Transaction, TransactionType, TransactionCategory
from app.services.transaction_service import TransactionService

bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')
transaction_service = TransactionService()

@bp.route('', methods=['GET'])
@jwt_required()
def get_transactions():
    """
    Get all transactions with optional filtering and pagination
    """
    current_user_id = get_jwt_identity()
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filters
    type_filter = request.args.get('type')
    category_filter = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    reconciled = request.args.get('reconciled')
    project_id = request.args.get('project_id')
    search = request.args.get('search')
    
    # Build query
    query = Transaction.query.filter_by(user_id=current_user_id)
    
    if type_filter:
        query = query.filter(Transaction.type == type_filter)
    
    if category_filter:
        query = query.filter(Transaction.category == category_filter)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= start_date)
        except ValueError:
            return jsonify({'message': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= end_date)
        except ValueError:
            return jsonify({'message': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    if reconciled is not None:
        query = query.filter(Transaction.is_reconciled == (reconciled.lower() == 'true'))
    
    if project_id:
        query = query.filter(Transaction.project_id == project_id)
    
    if search:
        search = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.description.ilike(search),
                Transaction.reference.ilike(search)
            )
        )
    
    # Order and paginate
    transactions = query.order_by(desc(Transaction.date), desc(Transaction.created_at))\
                       .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [t.to_dict() for t in transactions.items],
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': transactions.page
    })

@bp.route('/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get a single transaction by ID"""
    current_user_id = get_jwt_identity()
    
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        user_id=current_user_id
    ).first()
    
    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404
    
    return jsonify(transaction.to_dict())

@bp.route('', methods=['POST'])
@jwt_required()
def create_transaction():
    """Create a new transaction"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['date', 'amount', 'type', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    try:
        # Create transaction
        transaction = transaction_service.create_transaction(
            user_id=current_user_id,
            **data
        )
        
        return jsonify({
            'message': 'Transaction created successfully',
            'transaction': transaction.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Transaction creation error: {str(e)}')
        return jsonify({'message': 'Failed to create transaction'}), 500

@bp.route('/<int:transaction_id>', methods=['PUT'])
@jwt_required()
def update_transaction(transaction_id):
    """Update an existing transaction"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        user_id=current_user_id
    ).first()
    
    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404
    
    try:
        updated_transaction = transaction_service.update_transaction(
            transaction=transaction,
            **data
        )
        
        return jsonify({
            'message': 'Transaction updated successfully',
            'transaction': updated_transaction.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Transaction update error: {str(e)}')
        return jsonify({'message': 'Failed to update transaction'}), 500

@bp.route('/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    """Delete a transaction"""
    current_user_id = get_jwt_identity()
    
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        user_id=current_user_id
    ).first()
    
    if not transaction:
        return jsonify({'message': 'Transaction not found'}), 404
    
    try:
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({'message': 'Transaction deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Transaction deletion error: {str(e)}')
        return jsonify({'message': 'Failed to delete transaction'}), 500

@bp.route('/summary', methods=['GET'])
@jwt_required()
def get_transaction_summary():
    """Get transaction summary (totals by type/category)"""
    current_user_id = get_jwt_identity()
    
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build base query
    query = db.session.query(
        Transaction.type,
        Transaction.category,
        db.func.sum(Transaction.amount).label('total_amount')
    ).filter(Transaction.user_id == current_user_id)
    
    # Apply date filters if provided
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= start_date)
        except ValueError:
            return jsonify({'message': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= end_date)
        except ValueError:
            return jsonify({'message': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # Group by type and category
    results = query.group_by(Transaction.type, Transaction.category).all()
    
    # Format results
    summary = {
        'total_income': 0,
        'total_expenses': 0,
        'by_category': {},
        'by_type': {}
    }
    
    for type_, category, amount in results:
        amount = float(amount) if amount else 0
        
        # Update type totals
        if type_ not in summary['by_type']:
            summary['by_type'][type_] = 0
        summary['by_type'][type_] += amount
        
        # Update category totals
        if category not in summary['by_category']:
            summary['by_category'][category] = 0
        summary['by_category'][category] += amount
        
        # Update overall totals
        if type_ == 'income':
            summary['total_income'] += amount
        else:
            summary['total_expenses'] += amount
    
    summary['net_income'] = summary['total_income'] - summary['total_expenses']
    
    return jsonify(summary)
