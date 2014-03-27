
# Database and all the tables are defined here


from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

roles = db.Table('roles', db.Model.metadata,
	db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

class Role(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64))

	def __str__(self):
		return self.title

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)

	username = db.Column(db.String(32), unique=True)
	password_hash = db.Column(db.String(64))

	fullname = db.Column(db.String(64))
	status = db.Column(db.String(32)) 

	role = db.relationship('Role',secondary=roles, backref=db.backref('roles', lazy='dynamic'))

	def __str__(self):
		return self.fullname


class Device(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	gcm_token = db.Column(db.Text) # Yep, a gcm reg id could be 4k large
	created = db.Column(db.DateTime)

	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	user = db.relationship('User', backref = db.backref('devices', lazy='dynamic'))

	def __init__(self, *args, **kwargs):
		if not 'created' in kwargs:
			self.created = datetime.utcnow()

		super(Device, self).__init__(*args, **kwargs)

	def __str__(self):
		return 'Device %s' % self.id


class AccessToken(db.Model):
	"""An AccessToken is granted to devices in exchange for username and password.
	   It is used to access the api without passing passwords all the time"""

	id = db.Column(db.Integer, primary_key=True)
	
	token = db.Column(db.Unicode, unique=True)

	created = db.Column(db.DateTime)

	device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
	device = db.relationship('Device', backref = db.backref('tokens', lazy='dynamic'))



	def __init__(self, *args, **kwargs):
		if not 'created' in kwargs:
			self.created = datetime.utcnow()

		super(AccessToken, self).__init__(*args, **kwargs)

	
	def __str__(self):
		return 'AccessToken %s' % self.token


class LocatingRequest(db.Model):
	id = db.Column(db.Integer, primary_key=True)

	created = db.Column(db.DateTime)
	sent_successfully = db.Column(db.Boolean)

	requester_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	requester = db.relationship('User',
		backref = db.backref('requesting',lazy='select'),
		foreign_keys=[requester_id])

	target_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	target = db.relationship('User',
		backref = db.backref('targeted_by', lazy='select'),
		foreign_keys=[target_id])

	def __init__(self, *args, **kwargs):
		if not 'created' in kwargs:
			self.created = datetime.utcnow()

		super(LocatingRequest, self).__init__(*args, **kwargs)


	def __str__(self):
		return 'LocatingRequest #%s' % self.id


class Beacon(db.Model):
	id = db.Column(db.Integer, primary_key=True)

	uuid = db.Column(db.Unicode, unique=True)

	location = db.Column(db.Unicode)


	def __repr__(self):
		return '<Beacon %s:%s>' % (self.location, self.uuid)

	def __str__(self):
		return '%s: %s' % (self.location, self.uuid)

