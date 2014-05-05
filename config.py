# Override configuration parameters here for your local setup
# This file is not versioned.

import rootconfig


class ProductionConfig(rootconfig.ProductionConfig):
   	SQLALCHEMY_DATABASE_URI = 'sqlite://'

class DevelopmentConfig(rootconfig.DevelopmentConfig):
	SQLALCHEMY_DATABASE_URI = 'sqlite://'

class TestingConfig(rootconfig.TestingConfig):
    pass
