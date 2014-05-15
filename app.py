
# coding=UTF8
from flask import Flask, jsonify, request, abort, redirect, render_template, flash, url_for
from flask.ext.restless import APIManager
from flask.blueprints import Blueprint

from gcm import GCM
import os

#import config
from database import User, Device, db, Beacon, Role, LocatingRequest, AccessToken
from locator import locator_blueprint, LocatorService
from relay import relay_blueprint, RelayService
from messenger import GCMMessengerService
from authentication import AuthenticationService, authcheck_blueprint
import admin

from refactor import refactor_blueprint

#
# Rewriting for easier use with the testing framworks.
#
def create_app(debug=False):
    def load_env(env_name, conf_name = None):
        """Load the specified key to config from env if exists"""
        if conf_name is None:
            conf_name = env_name
        
        app.config[conf_name] = os.environ.get(env_name, app.config.get(conf_name))


    app = Flask(__name__)
    app.debug = debug

    app.config.from_object(os.environ.get('APP_CONFIG', 'config.DevelopmentConfig'))

    load_env('DATABASE_URL', 'SQLALCHEMY_DATABASE_URI')
    load_env('GCM_TOKEN')

    app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

    # Database creation
    db.init_app(app)
    with app.app_context():
        db.create_all()

    #
    # Create the services
    #
    gcm = GCM(app.config['GCM_TOKEN'])
    authService = AuthenticationService(db)
    messageService = GCMMessengerService(db, gcm)
    locatorService = LocatorService(db, messageService)
    relayService = RelayService(db, messageService)

    # Easy method to get currentuser
    def current_user():
        token = request.headers.get('Authorization')
        return authService.getUserFromAccessToken(token)

    #
    # Blueprints
    # 
    authcheckBlueprint = authcheck_blueprint(authService, locatorService)
    locatorBlueprint = locator_blueprint(db, locatorService, current_user)
    relayBlueprint = relay_blueprint(db, relayService, current_user)
    refBlueprint = refactor_blueprint(db, authService, app, current_user) # Needs app for now as it has the apimanager...
    app.register_blueprint(locatorBlueprint)
    app.register_blueprint(relayBlueprint)
    app.register_blueprint(authcheckBlueprint)
    app.register_blueprint(refBlueprint)
    
    # Create admin interface
    admin.init_app(app, messageService, locatorService)

    # I'm a teapot.
    @app.route("/")
    def index():
        abort(418)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host=app.config['HOST'], port=app.config['PORT'])

