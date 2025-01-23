# Copyright (c) 2019, Nxenv Technologies and Contributors
# License: MIT. See LICENSE
import requests

import nxenv
from nxenv.core.doctype.scheduled_job_type.scheduled_job_type import ScheduledJobType, sync_jobs
from nxenv.core.doctype.server_script.server_script import ServerScript
from nxenv.nxenvclient import NxenvClient, NxenvException
from nxenv.tests import IntegrationTestCase, UnitTestCase
from nxenv.utils import get_site_url

scripts = [
	dict(
		name="test_todo",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="ToDo",
		script="""
if "test" in doc.description:
	doc.status = 'Closed'
""",
	),
	dict(
		name="test_todo_validate",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="ToDo",
		script="""
if "validate" in doc.description:
	raise nxenv.ValidationError
""",
	),
	dict(
		name="test_api",
		script_type="API",
		api_method="test_server_script",
		allow_guest=1,
		script="""
nxenv.response['message'] = 'hello'
""",
	),
	dict(
		name="test_return_value",
		script_type="API",
		api_method="test_return_value",
		allow_guest=1,
		script="""
nxenv.flags = 'hello'
""",
	),
	dict(
		name="test_permission_query",
		script_type="Permission Query",
		reference_doctype="ToDo",
		script="""
conditions = '1 = 1'
""",
	),
	dict(
		name="test_invalid_namespace_method",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="Note",
		script="""
nxenv.method_that_doesnt_exist("do some magic")
""",
	),
	dict(
		name="test_todo_commit",
		script_type="DocType Event",
		doctype_event="Before Save",
		reference_doctype="ToDo",
		disabled=1,
		script="""
nxenv.db.commit()
""",
	),
	dict(
		name="test_add_index",
		script_type="DocType Event",
		doctype_event="Before Save",
		reference_doctype="ToDo",
		disabled=1,
		script="""
nxenv.db.add_index("Todo", ["color", "date"])
""",
	),
	dict(
		name="test_before_rename",
		script_type="DocType Event",
		doctype_event="After Rename",
		reference_doctype="Role",
		script="""
doc.desk_access =0
doc.save()
""",
	),
	dict(
		name="test_after_rename",
		script_type="DocType Event",
		doctype_event="After Rename",
		reference_doctype="Role",
		script="""
doc.disabled =1
doc.save()
""",
	),
]


class UnitTestServerScript(UnitTestCase):
	"""
	Unit tests for ServerScript.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestServerScript(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		nxenv.db.truncate("Server Script")
		nxenv.get_doc("User", "Administrator").add_roles("Script Manager")
		for script in scripts:
			script_doc = nxenv.get_doc(doctype="Server Script")
			script_doc.update(script)
			script_doc.insert()
		cls.enterClassContext(cls.enable_safe_exec())
		nxenv.db.commit()
		return super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		nxenv.db.commit()
		nxenv.db.truncate("Server Script")
		nxenv.client_cache.delete_value("server_script_map")

	def setUp(self):
		nxenv.client_cache.delete_value("server_script_map")

	def test_doctype_event(self):
		todo = nxenv.get_doc(doctype="ToDo", description="hello").insert()
		self.assertEqual(todo.status, "Open")

		todo = nxenv.get_doc(doctype="ToDo", description="test todo").insert()
		self.assertEqual(todo.status, "Closed")

		self.assertRaises(
			nxenv.ValidationError, nxenv.get_doc(doctype="ToDo", description="validate me").insert
		)

		role = nxenv.get_doc(doctype="Role", role_name="_Test Role 9").insert(ignore_if_duplicate=True)
		role.rename("_Test Role 10")
		role.reload()
		self.assertEqual(role.disabled, 1)
		self.assertEqual(role.desk_access, 0)

	def test_api(self):
		response = requests.post(get_site_url(nxenv.local.site) + "/api/method/test_server_script")
		self.assertEqual(response.status_code, 200)
		self.assertEqual("hello", response.json()["message"])

	def test_api_return(self):
		self.assertEqual(nxenv.get_doc("Server Script", "test_return_value").execute_method(), "hello")

	def test_permission_query(self):
		if nxenv.conf.db_type == "mariadb":
			self.assertTrue("where (1 = 1)" in nxenv.db.get_list("ToDo", run=False))
		else:
			self.assertTrue("where (1 = '1')" in nxenv.db.get_list("ToDo", run=False))
		self.assertTrue(isinstance(nxenv.db.get_list("ToDo"), list))

	def test_attribute_error(self):
		"""Raise AttributeError if method not found in Namespace"""
		note = nxenv.get_doc({"doctype": "Note", "title": "Test Note: Server Script"})
		self.assertRaises(AttributeError, note.insert)

	def test_syntax_validation(self):
		server_script = scripts[0]
		server_script["script"] = "js || code.?"

		with self.assertRaises(nxenv.ValidationError) as se:
			nxenv.get_doc(doctype="Server Script", **server_script).insert()

		self.assertTrue(
			"invalid python code" in str(se.exception).lower(), msg="Python code validation not working"
		)

	def test_commit_in_doctype_event(self):
		server_script = nxenv.get_doc("Server Script", "test_todo_commit")
		server_script.disabled = 0
		server_script.save()

		self.assertRaises(AttributeError, nxenv.get_doc(doctype="ToDo", description="test me").insert)

		server_script.disabled = 1
		server_script.save()

	def test_add_index_in_doctype_event(self):
		server_script = nxenv.get_doc("Server Script", "test_add_index")
		server_script.disabled = 0
		server_script.save()

		self.assertRaises(AttributeError, nxenv.get_doc(doctype="ToDo", description="test me").insert)

		server_script.disabled = 1
		server_script.save()

	def test_restricted_qb(self):
		todo = nxenv.get_doc(doctype="ToDo", description="QbScriptTestNote")
		todo.insert()

		script = nxenv.get_doc(
			doctype="Server Script",
			name="test_qb_restrictions",
			script_type="API",
			api_method="test_qb_restrictions",
			allow_guest=1,
			# whitelisted update
			script=f"""
nxenv.db.set_value("ToDo", "{todo.name}", "description", "safe")
""",
		)
		script.insert()
		script.execute_method()

		todo.reload()
		self.assertEqual(todo.description, "safe")

		# unsafe update
		script.script = f"""
todo = nxenv.qb.DocType("ToDo")
nxenv.qb.update(todo).set(todo.description, "unsafe").where(todo.name == "{todo.name}").run()
"""
		script.save()
		self.assertRaises(nxenv.PermissionError, script.execute_method)
		todo.reload()
		self.assertEqual(todo.description, "safe")

		# safe select
		script.script = f"""
todo = nxenv.qb.DocType("ToDo")
nxenv.qb.from_(todo).select(todo.name).where(todo.name == "{todo.name}").run()
"""
		script.save()
		script.execute_method()

	def test_scripts_all_the_way_down(self):
		# why not
		script = nxenv.get_doc(
			doctype="Server Script",
			name="test_nested_scripts_1",
			script_type="API",
			api_method="test_nested_scripts_1",
			script="""log("nothing")""",
		)
		script.insert()
		script.execute_method()

		script = nxenv.get_doc(
			doctype="Server Script",
			name="test_nested_scripts_2",
			script_type="API",
			api_method="test_nested_scripts_2",
			script="""nxenv.call("test_nested_scripts_1")""",
		)
		script.insert()
		script.execute_method()

	def test_server_script_rate_limiting(self):
		script1 = nxenv.get_doc(
			doctype="Server Script",
			name="rate_limited_server_script",
			script_type="API",
			enable_rate_limit=1,
			allow_guest=1,
			rate_limit_count=5,
			api_method="rate_limited_endpoint",
			script="""nxenv.flags = {"test": True}""",
		)

		script1.insert()

		script2 = nxenv.get_doc(
			doctype="Server Script",
			name="rate_limited_server_script2",
			script_type="API",
			enable_rate_limit=1,
			allow_guest=1,
			rate_limit_count=5,
			api_method="rate_limited_endpoint2",
			script="""nxenv.flags = {"test": False}""",
		)

		script2.insert()

		nxenv.db.commit()

		site = nxenv.utils.get_site_url(nxenv.local.site)
		client = NxenvClient(site)

		# Exhaust rate limit
		for _ in range(5):
			client.get_api(script1.api_method)

		self.assertRaises(NxenvException, client.get_api, script1.api_method)

		# Exhaust rate limit
		for _ in range(5):
			client.get_api(script2.api_method)

		self.assertRaises(NxenvException, client.get_api, script2.api_method)

		script1.delete()
		script2.delete()
		nxenv.db.commit()

	def test_server_script_scheduled(self):
		scheduled_script = nxenv.get_doc(
			doctype="Server Script",
			name="scheduled_script_wo_cron",
			script_type="Scheduler Event",
			script="""nxenv.flags = {"test": True}""",
			event_frequency="Hourly",
		).insert()

		cron_script = nxenv.get_doc(
			doctype="Server Script",
			name="scheduled_script_w_cron",
			script_type="Scheduler Event",
			script="""nxenv.flags = {"test": True}""",
			event_frequency="Cron",
			cron_format="0 0 1 1 *",  # 1st january
		).insert()

		# Ensure that jobs remain in DB after migrate
		sync_jobs()
		self.assertTrue(nxenv.db.exists("Scheduled Job Type", {"server_script": scheduled_script.name}))

		cron_job_name = nxenv.db.get_value("Scheduled Job Type", {"server_script": cron_script.name})
		self.assertTrue(cron_job_name)

		cron_job = nxenv.get_doc("Scheduled Job Type", cron_job_name)
		self.assertEqual(cron_job.next_execution.day, 1)
		self.assertEqual(cron_job.next_execution.month, 1)

		cron_script.cron_format = "0 0 2 1 *"  # 2nd january
		cron_script.save()

		updated_cron_job_name = nxenv.db.get_value("Scheduled Job Type", {"server_script": cron_script.name})
		updated_cron_job = nxenv.get_doc("Scheduled Job Type", updated_cron_job_name)
		self.assertEqual(updated_cron_job.next_execution.day, 2)

	def test_server_script_state_changes(self):
		script: ServerScript = nxenv.get_doc(
			doctype="Server Script",
			name="scheduled_script_state_change",
			script_type="Scheduler Event",
			script="""nxenv.flags = {"test": True}""",
			event_frequency="Hourly",
		).insert()

		job: ScheduledJobType = nxenv.get_doc("Scheduled Job Type", {"server_script": script.name})

		script.script_type = "API"
		script.save()
		self.assertTrue(job.reload().stopped)

		script.script_type = "Scheduler Event"
		script.save()
		self.assertFalse(job.reload().stopped)

		# Change to different frequency
		script.event_frequency = "Monthly"
		script.save()
		self.assertEqual(job.reload().frequency, "Monthly")

		# change cron expr
		script.event_frequency = "Cron"
		script.cron_format = "* * * * *"
		script.save()
		self.assertEqual(job.reload().frequency, "Cron")
		self.assertEqual(job.reload().cron_format, script.cron_format)

		# manually disable

		script.disabled = 1
		script.save()
		self.assertTrue(job.reload().stopped)

		script.disabled = 0
		script.save()
		self.assertFalse(job.reload().stopped)
