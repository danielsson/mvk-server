
from flask import jsonify, request, abort
from flask.blueprints import Blueprint

from database import User


class RelayService(object):
	""" docstring """
	def __init__(self, db, messager):
		super(RelayService, self).__init__()
		self.db = db
		self.messager = messager

	def sendData(self, target, payload):
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

		if 'data' not in data:
			abort(400) # Bad request, missing the data to send.
		
		payload = data['data']

		relService.sendData(target, payload)

		return jsonify(status="OK")

	return rs

