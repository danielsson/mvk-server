
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


#
# Initialize database
#
db.init_app(app)
if(app.config['DEBUG'] == True):
	with app.app_context():
		db.create_all()

#
# Blueprint for authchecking.
#
def authcheck_blueprint(authService):

	ac = Blueprint("authcheck", __name__)

	@ac.before_app_request
	def authcheck():
		return
		if '/admin' in request.path: return
		if request.path != '/api/login' and request.path != '/':
			token = request.headers.get('Authorization')
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
# Create the api
#
manager = APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Beacon, methods=['GET'])
manager.create_api(User, methods=['GET'], exclude_columns=['password_hash', 'devices', 'requesting', 'targeted_by'])


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
admin.register(User, session=db.session)
admin.register(Device, session=db.session)
admin.register(AccessToken, session=db.session)
admin.register(LocatingRequest, session=db.session)
admin.register(Beacon, session=db.session)
admin.init_app(app)

@app.route("/")
def index():
	return "Hello World"

if __name__ == '__main__':
	
	app.run(host=app.config['HOST'], port=app.config['PORT'])

