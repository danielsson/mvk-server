
# coding=UTF8
from flask import Flask, jsonify, request, abort, redirect
from flask.ext.restless import APIManager
from flask.blueprints import Blueprint
from flask.ext.superadmin import Admin

from gcm import GCM
import os

#import config
from database import User, Device, db, Beacon, Role, LocatingRequest, AccessToken
from locator import locator_blueprint, LocatorService
from relay import relay_blueprint, RelayService
from messenger import GCMMessengerService
from authentication import AuthenticationService, authcheck_blueprint

#
# Create the app
#
app = Flask(__name__)

def load_env(env_name, conf_name = None):
    """Load the specified key to config from env if exists"""
    if conf_name is None:
        conf_name = env_name
        
    app.config[conf_name] = os.environ.get(env_name, app.config[conf_name])


app.config.from_object(os.environ.get('APP_CONFIG', 'config.DevelopmentConfig'))

load_env('DATABASE_URL', 'SQLALCHEMY_DATABASE_URI')
load_env('GCM_TOKEN')

#
# Initialize database
#
db.init_app(app)
with app.app_context():
    db.create_all()


#
# Register the authentication blueprint
#
authService = AuthenticationService(db)

authcheckBlueprint = authcheck_blueprint(authService)
app.register_blueprint(authcheckBlueprint)


def current_user():
    token = request.headers.get('Authorization')
    return authService.getUserFromAccessToken(token)


#
# Preproccessor
#
def preproccessor(**kw):
    token = request.headers.get('Authorization')
    if token is None:
        abort(400)
    if authService.getUserFromAccessToken(token) is None:
        abort(403)
    return True


#
# Create the api
#
manager = APIManager(app, flask_sqlalchemy_db=db)

# Beacon
manager.create_api(
    Beacon,
    methods=['GET'],
    preprocessors=dict(GET_SINGLE=[preproccessor], GET_MANY=[preproccessor]))

# User
manager.create_api(
    User,
    methods=['GET'],
    exclude_columns=['password_hash', 'devices', 'requesting', 'targeted_by'],
    preprocessors=dict(GET_SINGLE=[preproccessor], GET_MANY=[preproccessor]))

@app.route('/api/user/me', methods=['GET'])
def getMe():
    user = current_user()
    adress = "/api/user/" + str(user.id)
    return redirect(adress)

#Get status
manager.create_api(
    User,
    methods=['GET'],
    collection_name='status',
    include_columns=['id', 'status'],
    preprocessors=dict(GET_SINGLE=[preproccessor], GET_MANY=[preproccessor]))


# Change status
@app.route('/api/status/set', methods=['POST'])
def setStatus():
    data = request.get_json()
    print data
    stat = data['status']
    if stat is None:
        abort(400) # Bad request
    token = request.headers.get('Authorization')
    user = authService.getUserFromAccessToken(token)
    if user is None:
        print "Wtf bbq"
    user.status = stat
    db.session.add(user)
    db.session.commit()
    return jsonify(status='OK')


# Logout
@app.route('/api/logout', methods=['POST'])
def out():
    token = request.headers.get('Authorization')
    authService.logout(token)
    return jsonify(status='OK')


# set Roles
@app.route('/api/role/set', methods=['POST'])
def setRole():
    token = request.headers.get('Authorization')
    user = authService.getUserFromAccessToken(token)
    data = request.get_json()
    if data is None or 'role' not in data:
        abort(400) # Bad request
    roles = data['role']
    previousroles = user.roles.all()

    # Remove all the roles that no longer exists
    for prole in previousroles:
        if prole.title not in roles:
            db.session.delete(prole)
    # Add all the new roles to the user
    for r in roles:
        datarole = Role.query.filter_by(title=r).first()
        if datarole is None:
            newrole = Role(title=r, user=[user])
            db.session.add(newrole)
        else:
            datarole.user.append(user)

    db.session.commit()
    return jsonify(status='OK')

# get Roles
manager.create_api(
    Role,
    methods=['GET'],
    collection_name='role',
    include_columns=['id','title','user','user.id'],
    preprocessors=dict(GET_SINGLE=[preproccessor], GET_MANY=[preproccessor]))

#
# Create the localization queue
#
gcm = GCM(app.config['GCM_TOKEN'])
messageService = GCMMessengerService(db, gcm)
locatorService = LocatorService(db, messageService)
relayService = RelayService(db, messageService)

locatorBlueprint = locator_blueprint(db, locatorService, current_user)
relayBlueprint = relay_blueprint(db, relayService, current_user)
app.register_blueprint(locatorBlueprint)
app.register_blueprint(relayBlueprint)

#
# Create admin interface
#
admin = Admin()
admin.register(Role, session=db.session)
admin.register(User, session=db.session)
admin.register(Device, session=db.session)
admin.register(AccessToken, session=db.session)
admin.register(LocatingRequest, session=db.session)
admin.register(Beacon, session=db.session)
admin.init_app(app)

#
# I'm a teapot.
# 
@app.route("/")
def index():
    abort(418)

if __name__ == '__main__':

    app.run(host=app.config['HOST'], port=app.config['PORT'])

