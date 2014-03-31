
# coding=UTF8
from flask import Flask, jsonify, request, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restless import APIManager
from flask.blueprints import Blueprint
from flask.ext.superadmin import Admin, model

from gcm import GCM
import os

from config import *
from database import *
from locator import locator_blueprint, LocatorService
from messenger import DummyMessengerService, GCMMessengerService
from authentication import DummyAuthenticationService, AuthenticationService

#
# Create the app
#
app = Flask(__name__)

cvar = os.environ.get('APP_CONFIG')
if cvar is not None:
	app.config.from_object(cvar)
else:
	app.config.from_object('config.DevelopmentConfig')

cvar = os.environ.get('DATABASE_URL')
if cvar is not None:
	app.config['SQLALCHEMY_DATABASE_URI'] = cvar

#
# Initialize database
#
db.init_app(app)
with app.app_context():
	db.create_all()

#
# Blueprint for authchecking.
#
def authcheck_blueprint(authService):

	ac = Blueprint("authcheck", __name__)

	#
	# A global check for all requests. Except for the root.
	# 
	@ac.before_app_request
	def authcheck():
		return
		if '/admin' in request.path: return # Allow acess to admin interface.
		if request.path != '/api/login' and request.path != '/':
			token = request.headers.get('Authorization') # Get the auth token
			if token == None:
				print "[AUTH] " + request.remote_addr + " missing token"
				abort(400) # Bad request
			if authService.getUserFromAccessToken(token) == None:
				print "[AUTH] " + request.remote_addr + " failed auth with token."
				abort(401) # Access denied

	@ac.route("/api/login", methods=['POST'])
	def login():
		data = request.get_json()
		if data == None or 'username' not in data or 'password' not in data:
			print "[LOGIN] " + request.remote_addr + " tried login without password or username"
			abort(400) # Bad request
		if 'gcm_token' not in data:
			print "[LOGIN] " + request.remote_addr + " missing gcm_token"
			abort(400) # Bad request, missing gcm token.
		user = authService.login(data['username'],data['password'])
		if user == None:
			print "[LOGIN] " + request.remote_addr + " tried login with not matching password/username"
			abort(403) # Access denied

		device = authService.getDevice(user,data['gcm_token'])
		accessToken = authService.createAccessToken(device)

		print "[LOGIN] " + request.remote_addr + " succesfully logged in"
		return jsonify(token=accessToken.token)

	return ac

#
# Register the authentication blueprint
#
authService = AuthenticationService(db)

authcheckBlueprint = authcheck_blueprint(authService)
app.register_blueprint(authcheckBlueprint)

#
# Preproccessor
#
def preproccessor(**kw):
	token = request.headers.get('Authorization')
	if token == None:
		abort(400)
	if authService.getUserFromAccessToken(token) == None:
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
	stat = data['status']
	if stat == None:
		abort(400) # Bad request
	token = request.headers.get('Authorization')
	user = authService.getUserFromAccessToken(token)
	user.status = stat
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
	if data == None:
		abort(400) # Bad request
	roles = data['role']
	if roles == None:
		abort(400) # Bad request

	previousroles = user.roles.all()

	# Remove all the roles that no longer exists
	for prole in previousroles:
		print prole.title
		if prole.title not in roles:
			print "removing " + prole.title + " from " + user.fullname
			# LINE THAT REMOVES THE ROLE THAT NO LONGER EXISTS FROM THE USER...
	# Add all the new roles to the user
	for r in roles:
		datarole = Role.query.filter_by(title=r).first()
		if datarole == None:
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
gcm = GCM('AIzaSyAtwU_pr-oaoI0bVBrQbUEWWDTI0wyN9Jg')
messageService = GCMMessengerService(db, gcm)
locatorService = LocatorService(db, messageService)

locatorBlueprint = locator_blueprint(db, locatorService)
app.register_blueprint(locatorBlueprint)

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

