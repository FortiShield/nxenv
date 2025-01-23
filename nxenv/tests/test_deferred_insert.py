import nxenv
from nxenv.deferred_insert import deferred_insert, save_to_db
from nxenv.tests import IntegrationTestCase


class TestDeferredInsert(IntegrationTestCase):
	def test_deferred_insert(self):
		route_history = {"route": nxenv.generate_hash(), "user": "Administrator"}
		deferred_insert("Route History", [route_history])

		save_to_db()
		self.assertTrue(nxenv.db.exists("Route History", route_history))

		route_history = {"route": nxenv.generate_hash(), "user": "Administrator"}
		deferred_insert("Route History", [route_history])
		nxenv.clear_cache()  # deferred_insert cache keys are supposed to be persistent
		save_to_db()
		self.assertTrue(nxenv.db.exists("Route History", route_history))
