# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import nxenv
from nxenv.core.doctype.doctype.doctype import clear_permissions_cache
from nxenv.model.db_query import DatabaseQuery
from nxenv.permissions import add_permission, reset_perms
from nxenv.tests import IntegrationTestCase, UnitTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = ["User"]


class UnitTestTodo(UnitTestCase):
	"""
	Unit tests for Todo.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestToDo(IntegrationTestCase):
	def test_delete(self):
		todo = nxenv.get_doc(doctype="ToDo", description="test todo", assigned_by="Administrator").insert()

		nxenv.db.delete("Deleted Document")
		todo.delete()

		deleted = nxenv.get_doc(
			"Deleted Document", dict(deleted_doctype=todo.doctype, deleted_name=todo.name)
		)
		self.assertEqual(todo.as_json(), deleted.data)

	def test_fetch(self):
		todo = nxenv.get_doc(doctype="ToDo", description="test todo", assigned_by="Administrator").insert()
		self.assertEqual(
			todo.assigned_by_full_name, nxenv.db.get_value("User", todo.assigned_by, "full_name")
		)

	def test_fetch_setup(self):
		nxenv.db.delete("ToDo")

		todo_meta = nxenv.get_meta("ToDo")
		todo_meta.get("fields", dict(fieldname="assigned_by_full_name"))[0].fetch_from = ""
		todo_meta.save()

		nxenv.clear_cache(doctype="ToDo")

		todo = nxenv.get_doc(doctype="ToDo", description="test todo", assigned_by="Administrator").insert()
		self.assertFalse(todo.assigned_by_full_name)

		todo_meta = nxenv.get_meta("ToDo")
		todo_meta.get("fields", dict(fieldname="assigned_by_full_name"))[
			0
		].fetch_from = "assigned_by.full_name"
		todo_meta.save()

		todo.reload()
		todo.save()

		self.assertEqual(
			todo.assigned_by_full_name, nxenv.db.get_value("User", todo.assigned_by, "full_name")
		)

	def test_todo_list_access(self):
		create_new_todo("Test1", "testperm@example.com")

		nxenv.set_user("test4@example.com")
		create_new_todo("Test2", "test4@example.com")
		test_user_data = DatabaseQuery("ToDo").execute()

		nxenv.set_user("testperm@example.com")
		system_manager_data = DatabaseQuery("ToDo").execute()

		self.assertNotEqual(test_user_data, system_manager_data)

		nxenv.set_user("Administrator")
		nxenv.db.rollback()

	def test_doc_read_access(self):
		# owner and assigned_by is testperm
		todo1 = create_new_todo("Test1", "testperm@example.com")
		test_user = nxenv.get_doc("User", "test4@example.com")

		# owner is testperm, but assigned_by is test4
		todo2 = create_new_todo("Test2", "test4@example.com")

		nxenv.set_user("test4@example.com")
		# owner and assigned_by is test4
		todo3 = create_new_todo("Test3", "test4@example.com")

		# user without any role to read or write todo document
		self.assertFalse(todo1.has_permission("read"))
		self.assertFalse(todo1.has_permission("write"))

		# user without any role but he/she is assigned_by of that todo document
		self.assertTrue(todo2.has_permission("read"))
		self.assertTrue(todo2.has_permission("write"))

		# user is the owner and assigned_by of the todo document
		self.assertTrue(todo3.has_permission("read"))
		self.assertTrue(todo3.has_permission("write"))

		nxenv.set_user("Administrator")

		test_user.add_roles("Blogger")
		add_permission("ToDo", "Blogger")

		nxenv.set_user("test4@example.com")

		# user with only read access to todo document, not an owner or assigned_by
		self.assertTrue(todo1.has_permission("read"))
		self.assertFalse(todo1.has_permission("write"))

		nxenv.set_user("Administrator")
		test_user.remove_roles("Blogger")
		reset_perms("ToDo")
		clear_permissions_cache("ToDo")
		nxenv.db.rollback()

	def test_fetch_if_empty(self):
		nxenv.db.delete("ToDo")

		# Allow user changes
		todo_meta = nxenv.get_meta("ToDo")
		field = todo_meta.get("fields", dict(fieldname="assigned_by_full_name"))[0]
		field.fetch_from = "assigned_by.full_name"
		field.fetch_if_empty = 1
		todo_meta.save()

		nxenv.clear_cache(doctype="ToDo")

		todo = nxenv.get_doc(
			doctype="ToDo",
			description="test todo",
			assigned_by="Administrator",
			assigned_by_full_name="Admin",
		).insert()

		self.assertEqual(todo.assigned_by_full_name, "Admin")

		# Overwrite user changes
		todo.meta.get("fields", dict(fieldname="assigned_by_full_name"))[0].fetch_if_empty = 0
		todo.meta.save()

		todo.reload()
		todo.save()

		self.assertEqual(
			todo.assigned_by_full_name, nxenv.db.get_value("User", todo.assigned_by, "full_name")
		)


def create_new_todo(description, assigned_by):
	todo = {"doctype": "ToDo", "description": description, "assigned_by": assigned_by}
	return nxenv.get_doc(todo).insert()
