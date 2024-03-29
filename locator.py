
# supplies the location request service.

from flask import jsonify, request, abort
from flask.blueprints import Blueprint

from database import User, Device, LocatingRequest

from datetime import datetime, timedelta

class LocatorService(object):
    """LocatorService provides methods to interact with the localization process"""

    def __init__(self, db, messager):
        super(LocatorService, self).__init__()
        self.db = db
        self.messager = messager

    def startLocating(self, target, requester):
        """Start locating the indicated individual. Returns True if
        a localization is already pending"""
        assert target != None and requester != None

        ongoing = LocatingRequest.query.filter_by(requester=requester, target=target).first()
        if ongoing != None:
            # We're already waiting, as there is already a request between us and target that has been sent.

            # If enough time has passed, allow us to send it again.
            if (datetime.utcnow() - ongoing.created) > timedelta(minutes=1):
                self.db.session.delete(ongoing) # Delete the already ongoing request.
            else:
                # Already a request sent in the last 1 minutes.
                return True

        # Has someone sent a succesful request to the person, but not received response?
        has_sent_locate_request = LocatingRequest.query.filter_by(target=target, sent_successfully=True).first()

        # If this exists, a message has been sent, and were done.
        was_sent_successfully = False
        if not has_sent_locate_request:
            was_sent_successfully = self.messager.requestTargetToIdentify(target, requester)
        else: 
            # For now do it anyways, as we want to notify the user of each request.
            was_sent_successfully = self.messager.requestTargetToIdentify(target, requester)

        # Put this request into the database
        req = LocatingRequest(requester=requester, target=target, sent_successfully=was_sent_successfully)
        self.db.session.add(req)
        self.db.session.commit()

        return was_sent_successfully


    def stopLocating(self, target):
        pending = LocatingRequest.query.filter_by(target=target).all()
        for p in pending:
            self.db.session.delete(p)
        self.db.session.commit()
        

    def notifyLocationFound(self, target, location):
        """Called when a target has notified its position"""
        assert None not in (target, location)

        requests = LocatingRequest.query.filter_by(target=target).all()

        # Lets notify all requesters of the location
        requesters = [x.requester for x in requests]

        self.messager.respondLocationFound(requesters, target, location)
        
        self.stopLocating(target)       

    def loggedInLetsAnswerEveryone(self, me):
        """ Called on login, checks for pending requests """
        # Check for requests that have yet to be sent.
        requests = LocatingRequest.query.filter_by(target=me, sent_successfully=False).all()
        # If there is no pending requests, do nothing.
        if requests is None:
            return False
        # Now that we are logged in resend these requests.
        for request in requests:
            # Only answer requests newer than 10 minutes.
            if request.created - datetime.utcnow() < timedelta(seconds=600):
                self.messager.requestTargetToIdentify(me, request.requester)
            else:
                # Delete requets older than 10 minutes.
                # TODO: maybe send that you did this to the client...
                self.db.session.delete(request)
                self.db.session.commit()
        return True


def locator_blueprint(db, locService, current_user):

    ls = Blueprint("Locator", __name__)


    @ls.route('/api/locate/request', methods=['POST'])
    def requestLocation():
        data = request.get_json()

        if data == None or 'target' not in data:
            abort(400) # Bad request

        target = User.query.get_or_404(data['target'])

        requester = current_user()

        locService.startLocating(target, requester)

        return jsonify(status='PENDING')

    @ls.route('/api/locate/notify', methods=['POST'])
    def notifyLocation():
        data = request.get_json()

        if data is None or 'location' not in data:
            abort(400)

        target = current_user()

        locService.notifyLocationFound(target, data['location'])

        return jsonify(status="OK")
    return ls









