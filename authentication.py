
from flask import request, abort, jsonify
from flask.blueprints import Blueprint
from database import AccessToken, Device, User
import hashlib
import os


# Authentication module for the app
class DummyAuthenticationService:
    def login(self, username, password):
        """Returns user if successful, else None"""
        return User(username='olof')

    def logout(self, token):
        pass

    def getUserFromAccessToken(self, token):
        return self.login(None, None)

    def getDevice(self, user, gcm_token):
        return Device(user=user, gcm_token=gcm_token)

    def createAccessToken(self, device):
        token = hashlib.sha256(os.urandom(16)).hexdigest()
        at = AccessToken(device=device, token=token)

        return at


class AuthenticationService(object):
    """docstring for AuthenticationService"""
    def __init__(self, db):
        super(AuthenticationService, self).__init__()
        self.db = db

    def login(self, username, password):
        """Returns user if successful, else None"""
        user = User.query.filter_by(username=username).first()

        if user is not None:
            pass_hash = hashlib.sha256(password).hexdigest()
            if user.password_hash == pass_hash:
                return user

        return None

    # delete accesstoken.
    def logout(self, token):
        t = AccessToken.query.filter_by(token=token).first()
        self.db.session.delete(t)
        self.db.session.commit()

    def clearDevice(self, device):
        self.db.session.delete(device)
        for t in device.tokens:
            self.logout(t.token) # remove the tokens.
        self.db.session.commit()

    def getUserFromAccessToken(self, token):
        at = AccessToken.query.filter_by(token=token).first()
        if at is None:
            return None

        return at.device.user

    def getDevice(self, user, gcm_token):
        device = Device.query.filter_by(gcm_token=gcm_token).first()
        if device is None:
            device = Device(user=user, gcm_token=gcm_token)

            self.db.session.add(device)
            self.db.session.commit()

        return device

    def createAccessToken(self, device):

        token = hashlib.sha256(os.urandom(16) + "iluvthabiebz").hexdigest()

        at = AccessToken(device=device, token=token)

        self.db.session.add(at)
        self.db.session.commit()

        return at

# Blueprint for authchecking.
#
def authcheck_blueprint(authService):

    ac = Blueprint("authcheck", __name__)

    #
    # A global check for all requests. Except for the root.
    #
    @ac.before_app_request
    def authcheck():
        if '/admin' in request.path:
            return # Allow acess to admin interface.
        if '/broadcast' in request.path:
            return
        if request.path != '/api/login' and request.path != '/':
            # Get the auth token
            token = request.headers.get('Authorization')
            if token is None:
                print "[AUTH] " + request.remote_addr + " missing token"
                abort(401)  # Bad request
            if authService.getUserFromAccessToken(token) is None:
                print "[AUTH] " + request.remote_addr + " failed auth with token."
                abort(401)  # Access denied

    @ac.route("/api/login", methods=['POST'])
    def login():
        data = request.get_json()
        if data is None or 'username' not in data or 'password' not in data:
            print "[LOGIN] " + request.remote_addr + " tried login without password or username"
            abort(400)  # Bad request
        if 'gcm_token' not in data:
            print "[LOGIN] " + request.remote_addr + " missing gcm_token"
            abort(400)  # Bad request, missing gcm token.
        user = authService.login(
            data['username'],
            data['password'])
        if user is None:
            print "[LOGIN] " + request.remote_addr + " tried login with not matching password/username"
            abort(403)  # Access denied

        gcm_token = data['gcm_token']

        # Remove previous accesstokens that are related to this device/gcm_token.
        device = Device.query.filter_by(gcm_token=gcm_token).first()
        authService.clearDevice(device)

        device = authService.getDevice(user, gcm_token)
        accesstoken = authService.createAccessToken(device)

        print "[LOGIN] " + request.remote_addr + " succesfully logged in"
        return jsonify(token=accesstoken.token)

    return ac
