""
This module contains the extensions used by the application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()

# Import models to ensure they are registered with SQLAlchemy
# This import must be at the bottom to avoid circular imports
from app.models import user, client, project, transaction, invoice  # noqa
