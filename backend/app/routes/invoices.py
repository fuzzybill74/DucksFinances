from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import desc, or_

from app import db
from app.models import Invoice, InvoiceStatus, InvoiceItem
from app.services.invoice_service import InvoiceService

bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')
invoice_service = InvoiceService()

@bp.route('', methods=['GET'])
@jwt_required()
def get_invoices():
    """
    Get all invoices with optional filtering and pagination
    """
    current_user_id = get_jwt_identity()
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filters
    status_filter = request.args.get('status')
    client_id = request.args.get('client_id')
    project_id = request.args.get('project_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')
    
    # Build query
    query = Invoice.query.filter_by(user_id=current_user_id)
    
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    if client_id:
        query = query.filter(Invoice.client_id == client_id)
    
    if project_id:
        query = query.filter(Invoice.project_id == project_id)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Invoice.issue_date >= start_date)
        except ValueError:
            return jsonify({'message': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Invoice.issue_date <= end_date)
        except ValueError:
            return jsonify({'message': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    if search:
        search = f"%{search}%"
        query = query.filter(
            or_(
                Invoice.invoice_number.ilike(search),
                Invoice.notes.ilike(search),
                Invoice.terms.ilike(search)
            )
        )
    
    # Order and paginate
    invoices = query.order_by(desc(Invoice.issue_date), desc(Invoice.created_at))\
                   .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [i.to_dict() for i in invoices.items],
        'total': invoices.total,
        'pages': invoices.pages,
        'current_page': invoices.page
    })

@bp.route('/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    """Get a single invoice by ID"""
    current_user_id = get_jwt_identity()
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        user_id=current_user_id
    ).first()
    
    if not invoice:
        return jsonify({'message': 'Invoice not found'}), 404
    
    return jsonify(invoice.to_dict())

@bp.route('', methods=['POST'])
@jwt_required()
def create_invoice():
    """Create a new invoice"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['client_id', 'issue_date', 'due_date', 'items']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    if not isinstance(data.get('items'), list) or len(data['items']) == 0:
        return jsonify({'message': 'At least one invoice item is required'}), 400
    
    try:
        # Create invoice
        invoice = invoice_service.create_invoice(
            user_id=current_user_id,
            **data
        )
        
        return jsonify({
            'message': 'Invoice created successfully',
            'invoice': invoice.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Invoice creation error: {str(e)}')
        return jsonify({'message': 'Failed to create invoice'}), 500

@bp.route('/<int:invoice_id>', methods=['PUT'])
@jwt_required()
def update_invoice(invoice_id):
    """Update an existing invoice"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        user_id=current_user_id
    ).first()
    
    if not invoice:
        return jsonify({'message': 'Invoice not found'}), 404
    
    # Prevent updating certain fields if invoice is already paid/partially paid
    if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID]:
        # Only allow updating status, notes, and terms
        allowed_updates = {'status', 'notes', 'terms'}
        if any(field in data for field in data.keys() if field not in allowed_updates):
            return jsonify({
                'message': 'Cannot update paid/partially paid invoice details. Only status, notes, and terms can be updated.'
            }), 400
    
    try:
        updated_invoice = invoice_service.update_invoice(
            invoice=invoice,
            **data
        )
        
        return jsonify({
            'message': 'Invoice updated successfully',
            'invoice': updated_invoice.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Invoice update error: {str(e)}')
        return jsonify({'message': 'Failed to update invoice'}), 500

@bp.route('/<int:invoice_id>', methods=['DELETE'])
@jwt_required()
def delete_invoice(invoice_id):
    """Delete an invoice"""
    current_user_id = get_jwt_identity()
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        user_id=current_user_id
    ).first()
    
    if not invoice:
        return jsonify({'message': 'Invoice not found'}), 404
    
    # Prevent deleting paid invoices
    if invoice.status == InvoiceStatus.PAID:
        return jsonify({'message': 'Cannot delete a paid invoice'}), 400
    
    try:
        db.session.delete(invoice)
        db.session.commit()
        return jsonify({'message': 'Invoice deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Invoice deletion error: {str(e)}')
        return jsonify({'message': 'Failed to delete invoice'}), 500

@bp.route('/<int:invoice_id>/send', methods=['POST'])
@jwt_required()
def send_invoice(invoice_id):
    """Send invoice to client via email"""
    current_user_id = get_jwt_identity()
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        user_id=current_user_id
    ).first()
    
    if not invoice:
        return jsonify({'message': 'Invoice not found'}), 404
    
    try:
        # Update status to SENT
        invoice.status = InvoiceStatus.SENT
        db.session.commit()
        
        # TODO: Implement email sending logic here
        # For now, just return success
        
        return jsonify({
            'message': 'Invoice sent successfully',
            'invoice': invoice.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error sending invoice: {str(e)}')
        return jsonify({'message': 'Failed to send invoice'}), 500

@bp.route('/<int:invoice_id>/record-payment', methods=['POST'])
@jwt_required()
def record_payment(invoice_id):
    """Record a payment for an invoice"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    if 'amount' not in data or 'payment_date' not in data:
        return jsonify({'message': 'Amount and payment_date are required'}), 400
    
    try:
        payment_amount = float(data['amount'])
        if payment_amount <= 0:
            return jsonify({'message': 'Amount must be greater than 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid amount'}), 400
    
    invoice = Invoice.query.filter_by(
        id=invoice_id,
        user_id=current_user_id
    ).first()
    
    if not invoice:
        return jsonify({'message': 'Invoice not found'}), 404
    
    if invoice.status == InvoiceStatus.VOID:
        return jsonify({'message': 'Cannot record payment for a void invoice'}), 400
    
    try:
        payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid payment_date format. Use YYYY-MM-DD'}), 400
    
    try:
        # Update invoice payment
        invoice.amount_paid += payment_amount
        invoice.calculate_totals()
        
        # Create a transaction for the payment
        from app.models import Transaction, TransactionType
        
        transaction = Transaction(
            date=payment_date,
            amount=payment_amount,
            description=f'Payment for invoice {invoice.invoice_number}',
            type=TransactionType.INCOME,
            category='service',
            invoice_id=invoice.id,
            project_id=invoice.project_id,
            user_id=current_user_id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment recorded successfully',
            'invoice': invoice.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error recording payment: {str(e)}')
        return jsonify({'message': 'Failed to record payment'}), 500

@bp.route('/summary', methods=['GET'])
@jwt_required()
def get_invoice_summary():
    """Get invoice summary (totals by status, etc.)"""
    current_user_id = get_jwt_identity()
    
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build base query
    query = Invoice.query.filter(Invoice.user_id == current_user_id)
    
    # Apply date filters if provided
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Invoice.issue_date >= start_date)
        except ValueError:
            return jsonify({'message': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Invoice.issue_date <= end_date)
        except ValueError:
            return jsonify({'message': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # Get all invoices
    invoices = query.all()
    
    # Calculate summary
    summary = {
        'total_invoices': len(invoices),
        'total_amount': 0,
        'total_paid': 0,
        'total_due': 0,
        'by_status': {},
        'by_client': {}
    }
    
    for invoice in invoices:
        # Update status counts
        status = invoice.status.value
        if status not in summary['by_status']:
            summary['by_status'][status] = {
                'count': 0,
                'amount': 0
            }
        
        summary['by_status'][status]['count'] += 1
        summary['by_status'][status]['amount'] += float(invoice.total or 0)
        
        # Update client totals
        client_name = invoice.client.name if invoice.client else 'Unknown'
        if client_name not in summary['by_client']:
            summary['by_client'][client_name] = {
                'count': 0,
                'amount': 0
            }
        
        summary['by_client'][client_name]['count'] += 1
        summary['by_client'][client_name]['amount'] += float(invoice.total or 0)
        
        # Update totals
        summary['total_amount'] += float(invoice.total or 0)
        summary['total_paid'] += float(invoice.amount_paid or 0)
        summary['total_due'] += float(invoice.amount_due or 0)
    
    return jsonify(summary)
