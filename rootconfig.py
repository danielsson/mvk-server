# This is the default value file.
# Put installation-specific in config.py



class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db'
    PORT = 8080
    SECRET_KEY="kjbjbkkbj"

class ProductionConfig(Config):
    DATABASE_URI = 'mysql://user@localhost/foo'
    PORT = 80

class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 8080

class TestingConfig(DevelopmentConfig):
    TESTING = True
