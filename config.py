# Override configuration parameters here for your local setup
# This file is not versioned.

import rootconfig


class ProductionConfig(rootconfig.ProductionConfig):
   	pass

class DevelopmentConfig(rootconfig.DevelopmentConfig):
	pass

class TestingConfig(rootconfig.TestingConfig):
    pass
