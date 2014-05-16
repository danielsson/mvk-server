# OBS PLEASE DO NOT WRITE NEW TESTS HERE, PLEASE WRITE THEM IN NEWTESTS.PY. 

# coding=UTF8
from database import Device, LocatingRequest, Role, User, db
from authentication import _hash, HASH_SALT, AuthenticationService
from app import app
from hashlib import sha256
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
# 7. Now it is ready to run the tests. Run them with the command: "python tests.py -v" (The v is for running it in verbose mode)
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
    def test_inherit(self):
        self.assertEquals(self.message, "Hello world")

    # Will always fail.
    @unittest.expectedFailure
    def test_fail(self):
        self.assertEquals(1, 2, "broken")
#
# End of examples tests.
#

#
# Add more example tests below
#


################### DATABASE TESTS ########################

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

class DatabaseTests(DatabaseTests):
    

    def test_1(self):
        
        self.phone = Device.query.get(self.phoneId)
        oldCreated = self.phone.created 

        self.phone.gcm_token = u"ouigöi"

        db.session.add(self.phone)
        db.session.commit();

        self.assertEquals(self.phone.created, oldCreated)

######################### AUTHENTICATION TESTS #################################

class HashTests(unittest.TestCase):
    # A very simple test
    def testHash(self):
        correctHash = sha256("Hello world" + HASH_SALT)
        authHash = _hash("Hello world")
        self.assertEquals(authHash.hexdigest(), correctHash.hexdigest())

    @unittest.expectedFailure
    def testFailHash(self):
        notCorrectHash = sha256("kittens" + HASH_SALT)
        authHash = _hash("Hello world")
        self.assertEquals(authHash.hexdigest(), correctHash.hexdigest())

# OBS: dependant on hashtest passing...
class AuthenticationTests(DatabaseTests):

    def setUp(self):
        super(AuthenticationTests, self).setUp()
        authService = AuthenticationService(db)

    def tearDown(self):
        super(AuthenticationTests, self).tearDown() 
        authService = None

    # The following tests needs to be written, usually needs more than one. For example one succesfull and one failing.
    # can be divided into class if deemed needed, for example if they would use the same setup & teardown methods.
    def testLogin(self):
        #TODO: write login tests
        #authService.login
        pass

    def testLogout(self):
        #TODO: write logout tests
        pass

    def testClearDevice(self):
        #TODO: write cleardevice tests
        pass

    def testGetUserFromAccessToken(self):
        #TODO: write getuser... tests
        pass

    def testGetDevice(self):
        #TODO: write getdevice tests
        pass

    def testCreateAccessToken(self):
        #TODO write createaccesstoken tests
        pass


########################### APP TESTS ################################3
# 
class appTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):        
        pass

    def testCurrentUser(self):
        pass


if __name__ == '__main__':
    with app.app_context():
        unittest.main()
