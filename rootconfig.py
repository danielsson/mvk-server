# This is the default value file.
# Put installation-specific in config.py



class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db'
    PORT = 8080
    SECRET_KEY="kjbjbkkbj"
    GCM_TOKEN="AIzaSyAtwU_pr-oaoI0bVBrQbUEWWDTI0wyN9Jg"
    HOST = '127.0.0.1'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://user@localhost/foo'
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False
    SECRET_KEY = "oajdspgjsejg63fgywtue7ri7wy"

class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 8080

class TestingConfig(DevelopmentConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
