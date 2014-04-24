
from flask import jsonify, request, abort
from flask.blueprints import Blueprint

from database import User


class RelayService(object):
	""" docstring """
	def __init__(self, db, messager):
		super(RelayService, self).__init__()
		self.db = db
		self.messager = messager

	def sendData(self, target, payload, action):
		self.messager.sendData(target, payload)

	def broadCast(self, targets, message):
		self.messager.sendBroadcast(targets, message)

def relay_blueprint(db, relService, current_user):

	rs = Blueprint("Relay", __name__)

	@rs.route('/api/relay/data', methods=['POST'])
	def sendData():
		print "data sending method"
		data = request.get_json()

		if data == None or 'target' not in data:
			abort(400) # Bad request

		target = User.query.get_or_404(data['target'])



		requester = current_user()

		if 'data' not in data or 'action' not in data:
			abort(400) # Bad request, missing the data or action
		
		payload = data['data']
		action = data['action']

		if action in ['BROADCAST', 'FOUND', 'BROADCAST']:
			print "action not allowed"
			abort(403) # Request okay, but not allowed action sent.

		relService.sendData(target, payload, action)

		return jsonify(status="OK")

	# XXX: THIS IS A TEMPORARY TEST METHOD. WILL BE REMOVED LATER!
	@rs.route('/api/relay/broadcast', methods=['POST'])
	def broadcast():
		print "broadcast method"
		data = request.get_json()

		if data == None or 'message' not in data:
			abort(400) # Bad request

		message = data['message']

		users = User.query.all()
		relService.broadCast(users, message)

		return jsonify(status="OK")

	return rs
