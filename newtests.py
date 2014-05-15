# coding=UTF8
from flask.ext.testing import TestCase
import unittest

from app import create_app
from database import db, User, Device, LocatingRequest

class baseCase(TestCase):
    def create_app(self): # do not know why this is needed.
        return create_app()

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

class moreTests(baseDataCase):

    def setUp(self): 
        super(moreTests, self).setUp()
        self.olof = User(username='olof', fullname='Olof Heden')
        self.phone = Device(gcm_token="123564", user=self.olof)
        db.session.add(self.phone)
        db.session.commit()
        self.phoneId = self.phone.id

    def tearDown(self):
        super(moreTests, self).tearDown()

    @unittest.expectedFailure
    def test1337(self):
        self.phone = Device.query.get(self.phoneId)
        self.assertEquals(self.phone.gcm_token, "1337")

    def test1338(self):
        self.phone = Device.query.get(self.phoneId)
        self.assertEquals(self.phone.gcm_token, "123564")

if __name__ == '__main__':
    unittest.main()