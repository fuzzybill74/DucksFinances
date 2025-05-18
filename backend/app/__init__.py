from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/*": {"origins": app.config['FRONTEND_URL']}})
    
    # Register blueprints
    from app.routes import auth, transactions, invoices, reports
    app.register_blueprint(auth.bp)
    app.register_blueprint(transactions.bp, url_prefix='/api/transactions')
    app.register_blueprint(invoices.bp, url_prefix='/api/invoices')
    app.register_blueprint(reports.bp, url_prefix='/api/reports')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Import models to ensure they are registered with SQLAlchemy
from app.models import user, transaction, invoice, client, project
