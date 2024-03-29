
from flask import jsonify, request, abort
from flask.blueprints import Blueprint

from database import User

# This file contains the method for relaying data to the client.
# the data in this case can be anything.
# The methods in the client using this method for sending data should be
# refactored to using a specific method of data transfer.

class RelayService(object):
	""" Provides methods that sends data to the client(s) """
	def __init__(self, db, messager):
		super(RelayService, self).__init__()
		self.db = db
		self.messager = messager

	def sendData(self, requester, target, payload, action):
		""" (Tries) sending the specifed data and action to the specifed client """
		self.messager.sendData(requester, target, payload, action)

	def broadCast(self, targets, message):
		""" Send messages to the specifed targets """
		self.messager.sendBroadcast(targets, message)

def relay_blueprint(db, relService, current_user):

	rs = Blueprint("Relay", __name__)

	@rs.route('/api/relay/data', methods=['POST'])
	def sendData():
		print "data sending method"
		data = request.get_json()

		if data == None or 'target' not in data:
			abort(400) # Bad request

		target = User.query.get_or_404(int(data['target']))
		requester = current_user()

		if 'data' not in data or 'action' not in data:
			abort(400) # Bad request, missing the data or action
		
		payload = data['data']
		action = data['action']

		# Check for actions that should be allowed to use, such that a location can't be faked.
		if action in ('BROADCAST', 'FOUND', 'BROADCAST', 'CHEESEIT'):
			print "action not allowed"
			abort(403) # Request okay, but not allowed action sent.

		relService.sendData(requester, target, payload, action)

		return jsonify(status="OK")
		
	return rs

