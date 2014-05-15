# coding=UTF8
from flask.ext.testing import TestCase
import unittest
from gcm import GCM

from messenger import GCMMessengerService
from locator import LocatorService
from app import create_app
from database import db, User, Device, LocatingRequest

class baseCase(TestCase):
    def create_app(self): # do not know why this is needed.
        self.app = create_app()
        return self.app

class baseDataCase(baseCase):
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class databaseTests(baseDataCase):

    def setUp(self):
        super(databaseTests, self).setUp()
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
        self.olofId = self.olof.id

    def tearDown(self):
        super(databaseTests, self).tearDown()

    def test001(self):
        pass

    def test002(self):
        self.phone = Device.query.get(self.phoneId)
        oldCreated = self.phone.created 

        self.phone.gcm_token = u"ouigöi"

        db.session.add(self.phone)
        db.session.commit();

        self.assertEquals(self.phone.created, oldCreated)

class locatorTests(baseDataCase):

    def setUp(self): 
        super(locatorTests, self).setUp()
        self.olof = User(username='olof', fullname='Olof Heden')
        self.ida = User(username='ida', fullname='Ida Azhimeme')
        self.phone = Device(gcm_token="123456", user=self.olof)
        db.session.add(self.phone)
        db.session.commit()
        self.phoneId = self.phone.id

        # stuff
        gcm = GCM(self.app.config['GCM_TOKEN'])
        self.mesService = GCMMessengerService(db, gcm)
        self.locService = LocatorService(db, self.mesService)

    def tearDown(self):
        super(locatorTests, self).tearDown()

    def testStartLocating(self):
        pass # Can't be written for now due to not always having valid gcm stuff.


if __name__ == '__main__':
    unittest.main()