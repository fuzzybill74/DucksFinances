from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime

from app import db
from app.models.user import User, UserRole

class AuthService:
    """Service for handling authentication and authorization logic"""
    
    def register_user(self, email, password, first_name, last_name, role=UserRole.STAFF):
        """
        Register a new user
        
        Args:
            email (str): User's email
            password (str): Plain text password
            first_name (str): User's first name
            last_name (str): User's last name
            role (UserRole, optional): User role. Defaults to UserRole.STAFF.
            
        Returns:
            User: The created user object
            
        Raises:
            ValueError: If email is already registered
        """
        if User.query.filter_by(email=email).first():
            raise ValueError('Email already registered')
        
        user = User(
            email=email,
            password=password,  # Password will be hashed in the model
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    def authenticate_user(self, email, password):
        """
        Authenticate a user
        
        Args:
            email (str): User's email
            password (str): Plain text password
            
        Returns:
            tuple: (user, tokens) if authentication successful, (None, None) otherwise
        """
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return None, None
            
        if not user.is_active:
            return None, None
            
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate tokens
        tokens = self._generate_auth_tokens(user)
        
        return user, tokens
    
    def refresh_token(self, user_id):
        """
        Refresh access token
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: New access token and user info
        """
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return None
            
        access_token = create_access_token(identity=user.id)
        return {
            'access_token': access_token,
            'user': user.to_dict()
        }
    
    def change_password(self, user, current_password, new_password):
        """
        Change user's password
        
        Args:
            user (User): User object
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            bool: True if password was changed, False otherwise
        """
        if not user.check_password(current_password):
            return False
            
        user.set_password(new_password)
        db.session.commit()
        return True
    
    def _generate_auth_tokens(self, user):
        """
        Generate JWT tokens for a user
        
        Args:
            user (User): User object
            
        Returns:
            dict: Dictionary containing access and refresh tokens
        """
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
