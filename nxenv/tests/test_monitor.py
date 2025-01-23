# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
import nxenv.monitor
from nxenv.monitor import MONITOR_REDIS_KEY, get_trace_id
from nxenv.tests import IntegrationTestCase
from nxenv.utils import set_request
from nxenv.utils.response import build_response


class TestMonitor(IntegrationTestCase):
	def setUp(self):
		nxenv.conf.monitor = 1
		nxenv.cache.delete_value(MONITOR_REDIS_KEY)

	def tearDown(self):
		nxenv.conf.monitor = 0
		nxenv.cache.delete_value(MONITOR_REDIS_KEY)

	def test_enable_monitor(self):
		set_request(method="GET", path="/api/method/nxenv.ping")
		response = build_response("json")

		nxenv.monitor.start()
		nxenv.monitor.stop(response)

		logs = nxenv.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = nxenv.parse_json(logs[0].decode())
		self.assertTrue(log.duration)
		self.assertTrue(log.site)
		self.assertTrue(log.timestamp)
		self.assertTrue(log.uuid)
		self.assertTrue(log.request)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_no_response(self):
		set_request(method="GET", path="/api/method/nxenv.ping")

		nxenv.monitor.start()
		nxenv.monitor.stop(response=None)

		logs = nxenv.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = nxenv.parse_json(logs[0].decode())
		self.assertEqual(log.request["status_code"], 500)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_job(self):
		nxenv.utils.background_jobs.execute_job(
			nxenv.local.site, "nxenv.ping", None, None, {}, is_async=False
		)

		logs = nxenv.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)
		log = nxenv.parse_json(logs[0].decode())
		self.assertEqual(log.transaction_type, "job")
		self.assertTrue(log.job)
		self.assertEqual(log.job["method"], "nxenv.ping")
		self.assertEqual(log.job["scheduled"], False)
		self.assertEqual(log.job["wait"], 0)

	def test_flush(self):
		set_request(method="GET", path="/api/method/nxenv.ping")
		response = build_response("json")
		nxenv.monitor.start()
		nxenv.monitor.stop(response)

		open(nxenv.monitor.log_file(), "w").close()
		nxenv.monitor.flush()

		with open(nxenv.monitor.log_file()) as f:
			logs = f.readlines()

		self.assertEqual(len(logs), 1)
		log = nxenv.parse_json(logs[0])
		self.assertEqual(log.transaction_type, "request")

	def test_trace_ids(self):
		set_request(method="GET", path="/api/method/nxenv.ping")
		response = build_response("json")
		nxenv.monitor.start()
		nxenv.db.sql("select 1")
		self.assertIn(get_trace_id(), str(nxenv.db.last_query))
		nxenv.monitor.stop(response)
