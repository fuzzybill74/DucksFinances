from .base import Config

class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '../../instance/dev.db')
    
    # Disable CSRF protection in development for easier API testing
    WTF_CSRF_ENABLED = False
    
    # Allow all origins in development
    CORS_ORIGINS = '*'
