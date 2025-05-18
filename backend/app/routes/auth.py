from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

from app import db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

bp = Blueprint('auth', __name__)
auth_service = AuthService()

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    try:
        # Create new user
        user = User(
            email=data['email'],
            password=data['password'],  # Password will be hashed in the model
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole.ADMIN  # First user is admin
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        tokens = user.generate_auth_tokens()
        
        return jsonify({
            'message': 'User registered successfully',
            **tokens
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Registration error: {str(e)}')
        return jsonify({'message': 'Failed to register user'}), 500

@bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'message': 'Account is deactivated'}), 403
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate tokens
    tokens = user.generate_auth_tokens()
    
    return jsonify({
        'message': 'Login successful',
        **tokens
    })

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'message': 'User not found or inactive'}), 401
    
    access_token = create_access_token(identity=current_user_id)
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    })

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user's profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
        
    return jsonify(user.to_dict())

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user's password"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'message': 'Current and new password are required'}), 400
    
    user = User.query.get(current_user_id)
    
    if not user or not user.check_password(data['current_password']):
        return jsonify({'message': 'Current password is incorrect'}), 400
    
    try:
        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Password change error: {str(e)}')
        return jsonify({'message': 'Failed to update password'}), 500
