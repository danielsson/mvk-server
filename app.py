
# coding=UTF8
from flask import Flask, jsonify, request, abort, redirect, render_template, flash, url_for
from flask.ext.restless import APIManager
from flask.blueprints import Blueprint
from flask.ext.superadmin import Admin, BaseView, expose

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
    
    app.config[conf_name] = os.environ.get(env_name, app.config.get(conf_name))


app.config.from_object(os.environ.get('APP_CONFIG', 'config.DevelopmentConfig'))

load_env('DATABASE_URL', 'SQLALCHEMY_DATABASE_URI')
load_env('GCM_TOKEN')

app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

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
class BroadcastView(BaseView):
    @expose('/')
    def index(self):
        roles = Role.query.all()

        return self.render('broadcast.jade', roles=roles)

    @expose('/send', methods=['POST'])
    def send(self):
        role_id = request.form.get('role')
        message = request.form.get('message')

        if message is None or len(message) == 0:
            flash("You need to supply a message!")
            return redirect(url_for('.index'))

        if role_id is None:
            flash("You need to select which group to target!")
            return redirect(url_for('.index'))

        if role_id < 0:
            messageService.sendBroadcast(User.query.all(), message)
        else:
            role = Role.query.get(role_id)
            messageService.sendBroadcast(role.users, message)

        flash("Successfully sent message")
        return redirect(url_for('.index'))


class LocateView(BaseView):
    @expose('/')
    def index(self):
        users = User.query.all()

        return self.render('locate.jade', users=users)

    @expose('/send', methods=['POST'])
    def send(self):
        
        sender = User.query.get(request.form.get('sender', 1))
        target = User.query.get(request.form.get('target', 1))

        locatorService.startLocating(target, sender)

        flash('Started locating')
        return redirect(url_for('.index'))
    
    #@expose('/cheeseit')
    #def cheeseit(self):

        # messageService.sendCheesit(User.query.all())
        # flash('Delicious topping activated')
        # return redirect(url_for('.index'))

class DataView(BaseView):
    @expose('/')
    def index(self):
        users = User.query.all()

        return self.render('data.jade', users=users)

    @expose('/send', methods=['POST']) 
    def send(self):
        target = User.query.get(request.form.get('sender', 1))
        action = request.form.get('action')
        payload = request.form.get('payload')

        if action is None or len(action) == 0:
            flash("You need to supply an action!")
            return redirect(url_for('.index'))

        if payload is None or len(payload) == 0:
            flash("You need to supply a payload!")
            return redirect(url_for('.index'))

        flash('Successfully sent data')
        messageService.sendData(target, payload, action)



admin = Admin(name='LoKI')
admin.register(Role, session=db.session)
admin.register(User, session=db.session)
admin.register(Device, session=db.session)
admin.register(AccessToken, session=db.session)
admin.register(LocatingRequest, session=db.session)
admin.register(Beacon, session=db.session)

admin.add_view(BroadcastView(name='Broadcast', category='Tools'))
admin.add_view(LocateView(name='Locate', category='Tools'))
admin.add_view(DataView(name='Data', category='Tools'))

admin.init_app(app)

#
# I'm a teapot.
# 
@app.route("/")
def index():
    abort(418)


if __name__ == '__main__':

    app.run(host=app.config['HOST'], port=app.config['PORT'])

