
# coding=UTF8
from flask import Flask, jsonify, request, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restless import APIManager
from flask.blueprints import Blueprint
from flask.ext.superadmin import Admin, model

import config
from database import *
from locator import locator_blueprint, LocatorService
from messenger import DummyMessengerService
from authentication import DummyAuthenticationService, AuthenticationService

#
# Create the app
#
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

#
# Initialize database
#
db.init_app(app)
if(app.config['DEBUG'] == True):
	with app.app_context():
		db.create_all()

#
# Create the api
#
manager = APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Beacon, methods=['GET'])

#
# Blueprint for authchecking.
#
def authcheck_blueprint(authService):

	ac = Blueprint("authcheck", __name__)

	@ac.before_app_request
	def authcheck():
		if '/admin' in request.path: return
		if request.path != '/api/login':
			data = request.get_json()
			if data == None or 'token' not in data:
				abort(400) # Bad request
			if authService.getUserFromAccessToken(data['token']) == None:
				abort(401) # Access denied

	@ac.route("/api/login", methods=['POST'])
	def login():
		data = request.get_json()
		if data == None or 'username' not in data or 'password' not in data:
			abort(400) # Bad request
		if authService.login(data['username'],data['password']) == None:
			abort(403) # Access denied
		if 'gcm_token' not in data:
			abort(400) # Bad request, missing gcm token.
		
		user = User.query.filter_by(username=data['username']).first()
		if user is None:
			abort(404)

		device = authService.getDevice(user,data['gcm_token'])
		accessToken = authService.createAccessToken(device)

		return jsonify(token=accessToken.token)

	return ac

#
# Register the authentication blueprint
#
authService = DummyAuthenticationService()

authcheckBlueprint = authcheck_blueprint(authService)
app.register_blueprint(authcheckBlueprint)

#
# Create the localization queue
#
messageService = DummyMessengerService(1)
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

@app.route("/hello")
def hello():
	return "Hej världen"

# Test return of json
@app.route("/foobar")
def foobar():
	return jsonify(id=1,message='hello world')

if __name__ == '__main__':
	
	app.run(port=app.config['PORT'])

