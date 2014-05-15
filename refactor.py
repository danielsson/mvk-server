from flask import jsonify, request, abort, redirect
from flask.ext.restless import APIManager
from flask.blueprints import Blueprint

from database import User, Device, db, Beacon, Role, LocatingRequest, AccessToken

def refactor_blueprint(db, authService, app, current_user):

    rf = Blueprint("Refactor", __name__)

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

    @rf.route('/api/user/me', methods=['GET'])
    def getMe():
        user = current_user()
        adress = "/api/user/" + str(user.id)
        return redirect(adress)

    # Get status
    manager.create_api(
        User,
        methods=['GET'],
        collection_name='status',
        include_columns=['id', 'status'],
        preprocessors=dict(GET_SINGLE=[preproccessor], GET_MANY=[preproccessor]))

     # Change status
    @rf.route('/api/status/set', methods=['POST'])
    def setStatus():
        data = request.get_json()
        print data
        stat = data['status']
        if stat is None:
            abort(400) # Bad request
        user = current_user()
        if user is None:
            print "Wtf bbq"
        user.status = stat
        db.session.add(user)
        db.session.commit()
        return jsonify(status='OK')


    # Logout
    @rf.route('/api/logout', methods=['POST'])
    def out():
        token = request.headers.get('Authorization')
        authService.logout(token)
        return jsonify(status='OK')


    # set Roles
    @rf.route('/api/role/set', methods=['POST'])
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
                # Remove the user from user list in the role.
                prole.users.remove(user)
        # Add all the new roles to the user
        for r in roles:
            datarole = Role.query.filter_by(title=r).first()
            if datarole is None:
                newrole = Role(title=r, users=[user])
                db.session.add(newrole)
            else:
                datarole.users.append(user)

        db.session.commit()
        return jsonify(status='OK')

    # get Roles
    manager.create_api(
        Role,
        methods=['GET'],
        collection_name='role',
        include_columns=['id','title','user','user.id'],
        preprocessors=dict(GET_SINGLE=[preproccessor], GET_MANY=[preproccessor]))

    return rf
    

