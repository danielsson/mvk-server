
from gcm import GCM
from database import Device

# Class containing the GCM logic
gcm_time_to_live = 3600

class DummyMessengerService(object):
    """docstring for DummyMessenger"""
    def __init__(self):
        super(DummyMessengerService, self).__init__()
    
    def requestTargetToIdentify(self, target):
        #print 'Can somebody *please* tell', target.fullname, 'to stand up'
        return True

    def respondLocationFound(self, requestors, target, location):
        #print "We've found it!", target.fullname, 'was hiding at', location

        for req in requestors:
            pass
            #print "requested by", req.fullname

    def sendData(self, target, data, action):
        #print "Can somebody *please* give",  target.fullname, "this data"
        return True


class GCMMessengerService(DummyMessengerService):
    """GCMMessengerService sends important messages to recipients using GCM"""
    def __init__(self, db, gcm):
        super(GCMMessengerService, self).__init__()
        self.gcm = gcm
        self.db = db

    def requestTargetToIdentify(self, target, requester):
        #print 'Requesting to identify:', target.fullname

        data = {
            'action': 'LOCATE',
            'requester': requester.fullname
        }

        devices = target.devices.all()
        registration_ids = [x.gcm_token for x in devices if len(x.gcm_token) > 0]

        if len(registration_ids) == 0:
            print 'The user does not have any devices!'
            return False

        #print registration_ids, data
        response = self.gcm.json_request(
            collapse_key="LOCATE"+requester.fullname,
            time_to_live=gcm_time_to_live,
            registration_ids=registration_ids,
            data=data)
        self.handleGCMErrors(response)

        return True

    def respondLocationFound(self, requestors, target, location):
        #print 'Responding to', requestors

        reg_ids = []

        for requester in requestors:
            for device in requester.devices:
                reg_ids.append(device.gcm_token)

        if len(reg_ids) == 0:
            print "No requestors for notify"
            return False

        data = {
            'action':'FOUND',
            'location':location,
            'user':target.id,
            'target': target.fullname
        }

        response = self.gcm.json_request(
            collapse_key="FOUND"+location,
            time_to_live=gcm_time_to_live,
            registration_ids=reg_ids,
            data=data)
        self.handleGCMErrors(response)

        return True

    def sendData(self, requester, target, payload, action):
        print "sending data"

        devices = target.devices.all()
        registration_ids = [x.gcm_token for x in devices if len(x.gcm_token) > 0]

        if len(registration_ids) == 0:
            print "The requested targets have no devices!"
            return False

        data = {
            'action': action,
            'requester': requester.id,
            'requester_fullname': requester.fullname,
            'data': payload
        }

        print registration_ids
        response = self.gcm.json_request(
            collapse_key=action,
            time_to_live=gcm_time_to_live,
            registration_ids=registration_ids,
            data=data)
        self.handleGCMErrors(response)

        return True

    def sendBroadcast(self, targets, message):

        # loop through all the targets and get the gcm tokens for them.
        devices = [] 
        for t in targets:
            devices.extend(t.devices.all())
        registration_ids = [x.gcm_token for x in devices if len(x.gcm_token) > 0]

        if len(registration_ids) == 0:
            print "The requested targets have no devices!"
            return False

        data = {
            'action': 'BROADCAST',
            'message': message
        }

        #print registration_ids, data
        response = self.gcm.json_request(
            collapse_key="BROADCAST"+message,
            time_to_live=gcm_time_to_live,
            registration_ids=registration_ids,
            data=data)
        self.handleGCMErrors(response)

        return True


    def sendCheesit(self, targets):

        # loop through all the targets and get the gcm tokens for them.
        devices = [] 
        for t in targets:
            devices.extend(t.devices.all())
        registration_ids = [x.gcm_token for x in devices if len(x.gcm_token) > 0]

        if len(registration_ids) == 0:
            print "The requested targets have no devices!"
            return False

        data = {
            'action': 'CHEESEIT'
        }

        #print registration_ids, data
        response = self.gcm.json_request(
            collapse_key="CHEESEIT",
            time_to_live=gcm_time_to_live,
            registration_ids=registration_ids,
            data=data)
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



