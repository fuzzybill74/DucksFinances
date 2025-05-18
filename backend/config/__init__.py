# Import all configuration classes
from .base import Config
from .development import DevelopmentConfig
from .testing import TestingConfig
from .production import ProductionConfig

# Create a dictionary to map config names to classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
