
from gcm import GCM
from database import Device

# Class containing the GCM logic

class DummyMessengerService(object):
    """docstring for DummyMessenger"""
    def __init__(self):
        super(DummyMessengerService, self).__init__()
    
    def requestTargetToIdentify(self, target):
        print "Can somebody *please* tell", target.fullname,  "to stand up"
        return True

    def respondLocationFound(self, requestors, target, location):
        print "We've found it!", target.fullname, "was hiding at", location

        for req in requestors:
            print "requested by", req.fullname


class GCMMessengerService(DummyMessengerService):
    """GCMMessengerService sends important messages to recipients using GCM"""
    def __init__(self, db, gcm):
        super(GCMMessengerService, self).__init__()
        self.gcm = gcm
        self.db = db

    def requestTargetToIdentify(self, target):
        print "Requesting to identify:", target.fullname

        data = {
            'action': 'LOCATE'
        }

        devices = target.devices.all()
        registration_ids = [x.gcm_token for x in devices if len(x.gcm_token) > 0]

        if len(registration_ids) == 0:
            print "The user", target.username, "does not have any devices!"
            return False

        print registration_ids, data
        response = self.gcm.json_request(registration_ids=registration_ids, data=data)
        self.handleGCMErrors(response)

        return True

    def respondLocationFound(self, requestors, target, location):
        print "Responding"

        reg_ids = [x.gcm_token for x in requestors if len(x.gcm_token) > 0]
        if len(reg_ids) == 0:
            print "No requestors for notify"
            return False

        data = {
            'action':'FOUND',
            'location':location
        }

        response = self.gcm.json_request(registration_ids=reg_ids, data=data)
        self.handleGCMErrors(response)

        return True





    def handleGCMErrors(self, response):
        if 'errors' in response:
            print "GCM errored"
            print response

            for error, reg_ids in response['errors'].items():
                if error is 'NotRegistered':
                    for rid in reg_ids:
                        print "Removing the following deviceid:", rid
                        device = Device.query.filter_by(gcm_token=reg_id).first()
                        if device != None:
                            device.gcm_token = ''
                            self.db.session.add(device)

            self.db.session.commit()


        if 'canonical' in response:
            commit_required = False

            for reg_id, canonical_id in response['canonical'].items():
                device = Device.query.filter_by(gcm_token=reg_id).first()
                if device != None:
                    device.gcm_token = canonical_id
                    self.db.session.add(device)
                    commit_required = True

            if commit_required:
                self.db.session.commit()



