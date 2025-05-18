""
DucksFinances - A bookkeeping application for small IT businesses
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException

# Import extensions
from app.extensions import db, migrate, jwt, ma

# Import models for Flask-Migrate
from app.models import user, client, project, transaction, invoice

def create_app(config_name=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    
    # Enable CORS
    CORS(app, resources={
        r"/*": {
            "origins": app.config.get('CORS_ORIGINS', '*')
        }
    })
    
    # Register blueprints
    from app.routes import auth, transactions, invoices, reports, clients, projects
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(transactions.bp, url_prefix='/api/transactions')
    app.register_blueprint(invoices.bp, url_prefix='/api/invoices')
    app.register_blueprint(reports.bp, url_prefix='/api/reports')
    app.register_blueprint(clients.bp, url_prefix='/api/clients')
    app.register_blueprint(projects.bp, url_prefix='/api/projects')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Internal server error'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            'success': False,
            'error': error.code,
            'message': error.description
        }), error.code
    
    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': user.User,
            'Client': client.Client,
            'Project': project.Project,
            'Transaction': transaction.Transaction,
            'Invoice': invoice.Invoice
        }
    
    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
