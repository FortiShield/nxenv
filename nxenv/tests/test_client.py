# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors

from unittest.mock import patch

import nxenv
from nxenv.tests import IntegrationTestCase
from nxenv.utils import get_site_url


class TestClient(IntegrationTestCase):
	def test_set_value(self):
		todo = nxenv.get_doc(doctype="ToDo", description="test").insert()
		nxenv.set_value("ToDo", todo.name, "description", "test 1")
		self.assertEqual(nxenv.get_value("ToDo", todo.name, "description"), "test 1")

		nxenv.set_value("ToDo", todo.name, {"description": "test 2"})
		self.assertEqual(nxenv.get_value("ToDo", todo.name, "description"), "test 2")

	def test_delete(self):
		from nxenv.client import delete
		from nxenv.desk.doctype.note.note import Note

		note = nxenv.get_doc(
			doctype="Note",
			title=nxenv.generate_hash(length=8),
			content="test",
			seen_by=[{"user": "Administrator"}],
		).insert()

		child_row_name = note.seen_by[0].name

		with patch.object(Note, "save") as save:
			delete("Note Seen By", child_row_name)
			save.assert_called()

		delete("Note", note.name)

		self.assertFalse(nxenv.db.exists("Note", note.name))
		self.assertRaises(nxenv.DoesNotExistError, delete, "Note", note.name)
		self.assertRaises(nxenv.DoesNotExistError, delete, "Note Seen By", child_row_name)

	def test_http_valid_method_access(self):
		from nxenv.client import delete
		from nxenv.handler import execute_cmd

		nxenv.set_user("Administrator")

		nxenv.local.request = nxenv._dict()
		nxenv.local.request.method = "POST"

		nxenv.local.form_dict = nxenv._dict(
			{"doc": dict(doctype="ToDo", description="Valid http method"), "cmd": "nxenv.client.save"}
		)
		todo = execute_cmd("nxenv.client.save")

		self.assertEqual(todo.get("description"), "Valid http method")

		delete("ToDo", todo.name)

	def test_http_invalid_method_access(self):
		from nxenv.handler import execute_cmd

		nxenv.set_user("Administrator")

		nxenv.local.request = nxenv._dict()
		nxenv.local.request.method = "GET"

		nxenv.local.form_dict = nxenv._dict(
			{"doc": dict(doctype="ToDo", description="Invalid http method"), "cmd": "nxenv.client.save"}
		)

		self.assertRaises(nxenv.PermissionError, execute_cmd, "nxenv.client.save")

	def test_run_doc_method(self):
		from nxenv.handler import execute_cmd

		report = nxenv.get_doc(
			{
				"doctype": "Report",
				"ref_doctype": "User",
				"report_name": nxenv.generate_hash(),
				"report_type": "Query Report",
				"is_standard": "No",
				"roles": [{"role": "System Manager"}],
			}
		).insert()

		nxenv.local.request = nxenv._dict()
		nxenv.local.request.method = "GET"

		# Whitelisted, works as expected
		nxenv.local.form_dict = nxenv._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "toggle_disable",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		execute_cmd(nxenv.local.form_dict.cmd)

		# Not whitelisted, throws permission error
		nxenv.local.form_dict = nxenv._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "create_report_py",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		self.assertRaises(nxenv.PermissionError, execute_cmd, nxenv.local.form_dict.cmd)

	def test_array_values_in_request_args(self):
		import requests

		from nxenv.auth import CookieManager, LoginManager

		nxenv.utils.set_request(path="/")
		nxenv.local.cookie_manager = CookieManager()
		nxenv.local.login_manager = LoginManager()
		nxenv.local.login_manager.login_as("Administrator")
		params = {
			"doctype": "DocType",
			"fields": ["name", "modified"],
			"sid": nxenv.session.sid,
		}
		headers = {
			"accept": "application/json",
			"content-type": "application/json",
		}
		url = get_site_url(nxenv.local.site)
		url += "/api/method/nxenv.client.get_list"

		res = requests.post(url, json=params, headers=headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		first_item = data["message"][0]
		self.assertTrue("name" in first_item)
		self.assertTrue("modified" in first_item)

	def test_client_get(self):
		from nxenv.client import get

		todo = nxenv.get_doc(doctype="ToDo", description="test").insert()
		filters = {"name": todo.name}
		filters_json = nxenv.as_json(filters)

		self.assertEqual(get("ToDo", filters=filters).description, "test")
		self.assertEqual(get("ToDo", filters=filters_json).description, "test")
		self.assertEqual(get("System Settings", "", "").doctype, "System Settings")
		self.assertEqual(get("ToDo", filters={}), get("ToDo", filters="{}"))
		todo.delete()

	def test_client_insert(self):
		from nxenv.client import insert

		def get_random_title():
			return f"test-{nxenv.generate_hash()}"

		# test insert dict
		doc = {"doctype": "Note", "title": get_random_title(), "content": "test"}
		note1 = insert(doc)
		self.assertTrue(note1)

		# test insert json
		doc["title"] = get_random_title()
		json_doc = nxenv.as_json(doc)
		note2 = insert(json_doc)
		self.assertTrue(note2)

		# test insert child doc without parent fields
		child_doc = {"doctype": "Note Seen By", "user": "Administrator"}
		with self.assertRaises(nxenv.ValidationError):
			insert(child_doc)

		# test insert child doc with parent fields
		child_doc = {
			"doctype": "Note Seen By",
			"user": "Administrator",
			"parenttype": "Note",
			"parent": note1.name,
			"parentfield": "seen_by",
		}
		note3 = insert(child_doc)
		self.assertTrue(note3)

		# cleanup
		nxenv.delete_doc("Note", note1.name)
		nxenv.delete_doc("Note", note2.name)

	def test_client_insert_many(self):
		from nxenv.client import insert, insert_many

		def get_random_title():
			return f"test-{nxenv.generate_hash(length=5)}"

		# insert a (parent) doc
		note1 = {"doctype": "Note", "title": get_random_title(), "content": "test"}
		note1 = insert(note1)

		doc_list = [
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{"doctype": "Note", "title": "not-a-random-title", "content": "test"},
			{"doctype": "Note", "title": get_random_title(), "content": "test"},
			{"doctype": "Note", "title": get_random_title(), "content": "test"},
			{"doctype": "Note", "title": "another-note-title", "content": "test"},
		]

		# insert all docs
		docs = insert_many(doc_list)

		self.assertEqual(len(docs), 7)
		self.assertEqual(nxenv.db.get_value("Note", docs[3], "title"), "not-a-random-title")
		self.assertEqual(nxenv.db.get_value("Note", docs[6], "title"), "another-note-title")
		self.assertIn(note1.name, docs)

		# cleanup
		for doc in docs:
			nxenv.delete_doc("Note", doc)
