# Override configuration parameters here for your local setup
# This file is not versioned.

import rootconfig


class ProductionConfig(rootconfig.ProductionConfig):
    pass

class DevelopmentConfig(rootconfig.DevelopmentConfig):
	GCM_TOKEN = 'AIzaSyAtwU_pr-oaoI0bVBrQbUEWWDTI0wyN9Jg'

class TestingConfig(rootconfig.TestingConfig):
    pass
