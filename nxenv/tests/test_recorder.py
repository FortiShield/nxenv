# Copyright (c) 2019, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import time

import sqlparse

import nxenv
import nxenv.recorder
from nxenv.recorder import normalize_query
from nxenv.tests import IntegrationTestCase, timeout
from nxenv.utils import set_request
from nxenv.utils.doctor import any_job_pending
from nxenv.website.serve import get_response_content


class TestRecorder(IntegrationTestCase):
	def setUp(self):
		self.wait_for_background_jobs()
		nxenv.recorder.stop()
		nxenv.recorder.delete()
		set_request()
		nxenv.recorder.start()
		nxenv.recorder.record()

	@timeout
	def wait_for_background_jobs(self):
		while any_job_pending(nxenv.local.site):
			time.sleep(1)

	def stop_recording(self):
		nxenv.recorder.dump()
		nxenv.recorder.stop()

	def test_start(self):
		self.stop_recording()
		requests = nxenv.recorder.get()
		self.assertEqual(len(requests), 1)

	def test_do_not_record(self):
		nxenv.recorder.do_not_record(nxenv.get_all)("DocType")
		self.stop_recording()
		requests = nxenv.recorder.get()
		self.assertEqual(len(requests), 0)

	def test_get(self):
		self.stop_recording()

		requests = nxenv.recorder.get()
		self.assertEqual(len(requests), 1)

		request = nxenv.recorder.get(requests[0]["uuid"])
		self.assertTrue(request)

	def test_delete(self):
		self.stop_recording()

		requests = nxenv.recorder.get()
		self.assertEqual(len(requests), 1)

		nxenv.recorder.delete()

		requests = nxenv.recorder.get()
		self.assertEqual(len(requests), 0)

	def test_record_without_sql_queries(self):
		self.stop_recording()

		requests = nxenv.recorder.get()
		request = nxenv.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"]), 0)

	def test_record_with_sql_queries(self):
		nxenv.get_all("DocType")
		self.stop_recording()

		requests = nxenv.recorder.get()
		request = nxenv.recorder.get(requests[0]["uuid"])

		self.assertNotEqual(len(request["calls"]), 0)

	def test_explain(self):
		nxenv.db.sql("SELECT * FROM tabDocType")
		nxenv.db.sql("COMMIT")
		nxenv.db.sql("select 1", run=0)
		self.stop_recording()

		requests = nxenv.recorder.get()
		request = nxenv.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"][0]["explain_result"]), 1)
		self.assertEqual(len(request["calls"][1]["explain_result"]), 0)

	def test_multiple_queries(self):
		queries = [
			{"mariadb": "SELECT * FROM tabDocType", "postgres": 'SELECT * FROM "tabDocType"'},
			{"mariadb": "SELECT COUNT(*) FROM tabDocType", "postgres": 'SELECT COUNT(*) FROM "tabDocType"'},
			{"mariadb": "COMMIT", "postgres": "COMMIT"},
		]

		sql_dialect = nxenv.db.db_type or "mariadb"
		for query in queries:
			nxenv.db.sql(query[sql_dialect])

		self.stop_recording()

		requests = nxenv.recorder.get()
		request = nxenv.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"]), len(queries))

		for query, call in zip(queries, request["calls"], strict=False):
			self.assertEqual(
				call["query"],
				sqlparse.format(
					query[sql_dialect].strip(), keyword_case="upper", reindent=True, strip_comments=True
				),
			)

	def test_duplicate_queries(self):
		queries = [
			("SELECT * FROM tabDocType", 2),
			("SELECT COUNT(*) FROM tabDocType", 1),
			("select * from tabDocType", 2),
			("COMMIT", 3),
			("COMMIT", 3),
			("COMMIT", 3),
		]
		for query in queries:
			nxenv.db.sql(query[0])

		self.stop_recording()

		requests = nxenv.recorder.get()
		request = nxenv.recorder.get(requests[0]["uuid"])

		for query, call in zip(queries, request["calls"], strict=False):
			self.assertEqual(call["exact_copies"], query[1])

	def test_error_page_rendering(self):
		content = get_response_content("error")
		self.assertIn("Error", content)


class TestRecorderDeco(IntegrationTestCase):
	def test_recorder_flag(self):
		nxenv.recorder.delete()

		@nxenv.recorder.record_queries
		def test():
			nxenv.get_all("User")

		test()
		self.assertTrue(nxenv.recorder.get())


class TestQueryNormalization(IntegrationTestCase):
	def test_query_normalization(self):
		test_cases = {
			"select * from user where name = 'x'": "select * from user where name = ?",
			"select * from user where a > 5": "select * from user where a > ?",
			"select * from `user` where a > 5": "select * from `user` where a > ?",
			"select `name` from `user`": "select `name` from `user`",
			"select `name` from `user` limit 10": "select `name` from `user` limit ?",
			"select `name` from `user` where name in ('a', 'b', 'c')": "select `name` from `user` where name in (?)",
		}

		for query, normalized in test_cases.items():
			self.assertEqual(normalize_query(query), normalized)
