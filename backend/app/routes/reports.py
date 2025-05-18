from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, extract, desc
from collections import defaultdict

from app import db
from app.models import Transaction, Invoice, TransactionType, InvoiceStatus

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/income-expense', methods=['GET'])
@jwt_required()
def income_expense_report():
    """
    Generate income vs expense report for a given date range
    """
    current_user_id = get_jwt_identity()
    
    # Get date range from query params (default to current year)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'month')  # month, week, day, year
    
    # Validate group_by parameter
    if group_by not in ['day', 'week', 'month', 'year']:
        return jsonify({'message': 'Invalid group_by parameter. Must be one of: day, week, month, year'}), 400
    
    # Set default date range if not provided
    if not start_date or not end_date:
        end_date = datetime.utcnow().date()
        start_date = end_date.replace(month=1, day=1)  # Start of current year
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Build the date part expression based on grouping
    if group_by == 'year':
        date_part = extract('year', Transaction.date).label('period')
    elif group_by == 'month':
        date_part = func.to_char(Transaction.date, 'YYYY-MM').label('period')
    elif group_by == 'week':
        date_part = func.to_char(Transaction.date, 'IYYY-IW').label('period')
    else:  # day
        date_part = func.date(Transaction.date).label('period')
    
    # Query transactions grouped by period and type
    transactions = db.session.query(
        date_part,
        Transaction.type,
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == current_user_id,
        Transaction.date.between(start_date, end_date)
    ).group_by(
        'period', Transaction.type
    ).order_by('period').all()
    
    # Process results into a structured format
    result = defaultdict(lambda: {
        'period': None,
        'income': 0.0,
        'expense': 0.0,
        'net': 0.0
    })
    
    for period, txn_type, amount in transactions:
        if period not in result:
            result[period]['period'] = period
        
        if txn_type == 'income':
            result[period]['income'] += float(amount or 0)
        else:
            result[period]['expense'] += float(amount or 0)
        
        result[period]['net'] = result[period]['income'] - result[period]['expense']
    
    # Convert to list and sort by period
    report_data = sorted(result.values(), key=lambda x: x['period'])
    
    # Calculate totals
    totals = {
        'total_income': sum(item['income'] for item in report_data),
        'total_expense': sum(item['expense'] for item in report_data),
        'net_income': 0
    }
    totals['net_income'] = totals['total_income'] - totals['total_expense']
    
    return jsonify({
        'data': report_data,
        'totals': totals,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'group_by': group_by
    })

@bp.route('/profit-loss', methods=['GET'])
@jwt_required()
def profit_loss_report():
    """
    Generate profit and loss report for a given date range
    """
    current_user_id = get_jwt_identity()
    
    # Get date range from query params (default to current year)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Set default date range if not provided
    if not start_date or not end_date:
        end_date = datetime.utcnow().date()
        start_date = end_date.replace(month=1, day=1)  # Start of current year
    else:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Query income transactions grouped by category
    income = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == current_user_id,
        Transaction.type == 'income',
        Transaction.date.between(start_date, end_date)
    ).group_by(Transaction.category).all()
    
    # Query expense transactions grouped by category
    expenses = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == current_user_id,
        Transaction.type == 'expense',
        Transaction.date.between(start_date, end_date)
    ).group_by(Transaction.category).all()
    
    # Calculate totals
    total_income = sum(float(amount or 0) for _, amount in income)
    total_expenses = sum(float(amount or 0) for _, amount in expenses)
    net_profit = total_income - total_expenses
    
    # Format response
    return jsonify({
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'income': [
            {'category': category, 'amount': float(amount or 0)}
            for category, amount in income
        ],
        'expenses': [
            {'category': category, 'amount': float(amount or 0)}
            for category, amount in expenses
        ],
        'totals': {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': net_profit
        }
    })

@bp.route('/cash-flow', methods=['GET'])
@jwt_required()
def cash_flow_report():
    """
    Generate cash flow report for a given date range
    """
    current_user_id = get_jwt_identity()
    
    # Get date range from query params (default to last 12 months)
    end_date = request.args.get('end_date')
    months = int(request.args.get('months', 12))
    
    # Set default end date if not provided
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    else:
        end_date = datetime.utcnow().date()
    
    # Calculate start date based on months
    if months <= 0:
        return jsonify({'message': 'Months must be greater than 0'}), 400
    
    start_date = (end_date - timedelta(days=30*months)).replace(day=1)
    
    # Generate all periods in the range
    periods = []
    current = start_date
    while current <= end_date:
        periods.append(current.strftime('%Y-%m'))
        # Move to first day of next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1, day=1)
        else:
            current = current.replace(month=current.month + 1, day=1)
    
    # Query income and expenses by month
    monthly_data = db.session.query(
        func.to_char(Transaction.date, 'YYYY-MM').label('month'),
        Transaction.type,
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == current_user_id,
        Transaction.date.between(start_date, end_date)
    ).group_by(
        'month', Transaction.type
    ).order_by('month').all()
    
    # Initialize data structure with all periods
    cash_flow = []
    for period in periods:
        cash_flow.append({
            'period': period,
            'income': 0.0,
            'expense': 0.0,
            'net': 0.0,
            'running_balance': 0.0
        })
    
    # Fill in the data
    for month, txn_type, amount in monthly_data:
        # Find the index of this month in our periods list
        try:
            idx = periods.index(month)
            if txn_type == 'income':
                cash_flow[idx]['income'] = float(amount or 0)
            else:
                cash_flow[idx]['expense'] = float(amount or 0)
            
            cash_flow[idx]['net'] = cash_flow[idx]['income'] - cash_flow[idx]['expense']
        except ValueError:
            continue  # Skip if month not in our periods (shouldn't happen with our query)
    
    # Calculate running balance
    running_balance = 0.0
    for period in cash_flow:
        running_balance += period['net']
        period['running_balance'] = running_balance
    
    # Calculate totals
    totals = {
        'total_income': sum(period['income'] for period in cash_flow),
        'total_expense': sum(period['expense'] for period in cash_flow),
        'net_cash_flow': sum(period['net'] for period in cash_flow),
        'ending_balance': running_balance
    }
    
    return jsonify({
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'data': cash_flow,
        'totals': totals
    })

@bp.route('/tax-summary', methods=['GET'])
@jwt_required()
def tax_summary_report():
    """
    Generate tax summary report for a given fiscal year
    """
    current_user_id = get_jwt_identity()
    
    # Get fiscal year (default to current year)
    fiscal_year = request.args.get('year', datetime.utcnow().year, type=int)
    
    # Define date range for the fiscal year (assuming calendar year for simplicity)
    start_date = datetime(fiscal_year, 1, 1).date()
    end_date = datetime(fiscal_year, 12, 31).date()
    
    # Query income and expenses for the year
    transactions = db.session.query(
        Transaction.type,
        Transaction.category,
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == current_user_id,
        Transaction.date.between(start_date, end_date)
    ).group_by(
        Transaction.type, Transaction.category
    ).all()
    
    # Process transactions into tax categories
    tax_categories = {
        'income': {
            'service': 0.0,
            'product_sale': 0.0,
            'other_income': 0.0,
            'total': 0.0
        },
        'expenses': {
            'office_supplies': 0.0,
            'rent': 0.0,
            'utilities': 0.0,
            'salary': 0.0,
            'contractor': 0.0,
            'software': 0.0,
            'hardware': 0.0,
            'travel': 0.0,
            'meals': 0.0,
            'marketing': 0.0,
            'professional_services': 0.0,
            'insurance': 0.0,
            'taxes': 0.0,
            'other_expense': 0.0,
            'total': 0.0
        },
        'net_profit': 0.0,
        'estimated_tax': 0.0
    }
    
    for txn_type, category, amount in transactions:
        amount_float = float(amount or 0)
        
        if txn_type == 'income':
            if category in tax_categories['income']:
                tax_categories['income'][category] += amount_float
            else:
                tax_categories['income']['other_income'] += amount_float
            tax_categories['income']['total'] += amount_float
        else:  # expense
            if category in tax_categories['expenses']:
                tax_categories['expenses'][category] += amount_float
            else:
                tax_categories['expenses']['other_expense'] += amount_float
            tax_categories['expenses']['total'] += amount_float
    
    # Calculate net profit and estimated tax (simplified)
    tax_categories['net_profit'] = tax_categories['income']['total'] - tax_categories['expenses']['total']
    tax_categories['estimated_tax'] = tax_categories['net_profit'] * 0.30  # 30% estimated tax rate (simplified)
    
    return jsonify({
        'fiscal_year': fiscal_year,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'tax_categories': tax_categories
    })
