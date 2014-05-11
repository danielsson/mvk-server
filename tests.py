
# coding=UTF8
from database import Device, LocatingRequest, Role, User, db
from app import app
import unittest

#################### TESTING INSTRUCTIONS #########################
# The seven steps you need to complete to run the tests.
# 1. Download and install python 2.7
# 2. If you do not have pip, download and install it.
# If the venv directory already exist. Go to step 6.
#   3. "pip install virtualenv"
#   4. "virtualenv venv"
#   5. "source venv/Scripts/activate" (for windows) "source venv/bin/activate" (for the rest)
# 6. Install the needed plugins, "pip install -r requirements_no_postgresql.txt" (may need sudo)
# 7. Now it is ready to run the tests. Run them with the command: "python tests.py"
###################################################################



#
# Here follows a few example tests.
#
class TestTest(unittest.TestCase):
    """ A testcase that is as simple as it gets """
    def setUp(self):
        self.message= "Hello world"

    def tearDown(self):
        pass # Add here for stuff that needs to be done after the test is done,
             # so it is ready for the next test.

    def test_001(self):
        pass # As simple as possible test. 
        # If this not pass something is wrong with the testing. Should never happen.

class TestInheritFromTest(TestTest):
    def test_inherit(self): # Uses the 
        print self.message
#
# End of examples tests.
#

#
# Add more example tests below
#

class DatabaseTests(unittest.TestCase):
    db.init_app(app)
    with app.app_context():
        db.create_all()

    def setUp(self):
        self.olof = User(username='olof', fullname='Olof Heden')
        self.ida = User(username='ida', fullname='Ida Azhimeme')

        self.phone = Device(gcm_token="123564", user=self.olof)

        self.lr = LocatingRequest(requester=self.ida, target=self.olof)

        db.session.add(self.olof)
        db.session.add(self.ida)
        db.session.add(self.phone)
        db.session.add(self.lr)

        db.session.commit()
        self.phoneId = self.phone.id

    def tearDown(self):
        db.session.delete(self.olof)
        db.session.delete(self.ida)
        db.session.delete(self.phone)
        db.session.delete(self.lr)

        db.session.commit()

    def test_1(self):
        
        self.phone = Device.query.get(self.phoneId)
        oldCreated = self.phone.created 

        self.phone.gcm_token = u"ouigöi"

        db.session.add(self.phone)
        db.session.commit();

        self.assertEquals(self.phone.created, oldCreated)




if __name__ == '__main__':
    with app.app_context():
        unittest.main()
