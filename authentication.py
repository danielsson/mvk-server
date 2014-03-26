
from database import AccessToken, Device, User
import hashlib, os

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


	def logout(self, token):
		t = AccessToken.query.filter_by(token=token).first()
		self.db.session.delete(t)
		self.db.session.commit()
		

	def getUserFromAccessToken(self, token):
		at = AccessToken.query.filter_by(token=token).first()
		if at is None: return None

		return at.device.user

	def getDevice(self, user, gcm_token):
		device = Device.query.filter_by(gcm_token=gcm_token).first()
		if device == None:
			device = Device(user=user, gcm_token=gcm_token)

			self.db.session.add(device)
			self.db.session.commit()

		return device

	def createAccessToken(self, device):

		token = hashlib.sha256(os.urandom(16) + "salt_asdfghjkl").hexdigest()

		at = AccessToken(device=device, token=token)

		self.db.session.add(at)
		self.db.session.commit()

		return at



