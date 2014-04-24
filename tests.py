
# coding=UTF8
from database import Device, LocatingRequest, Role, User
from app import app
import unittest

class DatabaseTests(unittest.TestCase):


    def setUp(self):
        self.olof = User(username='olof', fullname='Olof Heden', role=u'Överläkare')
        self.ida = User(username='ida', fullname='Ida Azhimeme', role=u'Sjukhusdirektör')

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


    def test_created(self):
        
        self.phone = Device.query.get(self.phoneId)
        oldCreated = self.phone.created 

        self.phone.gcm_token = u"ouigöi"

        db.session.add(self.phone)
        db.session.commit();

        self.assertEquals(self.phone.created, oldCreated)


class LocatorTest(unittest.TestCase):
    """docstring for LocatorTest"""
    def __init__(self, arg):
        super(LocatorTest, self).__init__()
        self.arg = arg
        
    def test_a():
        pass






if __name__ == '__main__':
    with app.app_context():
        unittest.main()
