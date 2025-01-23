# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.core.doctype.role.role import get_info_based_on_role
from nxenv.tests import IntegrationTestCase, UnitTestCase


class UnitTestRole(UnitTestCase):
	"""
	Unit tests for Role.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestUser(IntegrationTestCase):
	def test_disable_role(self):
		nxenv.get_doc("User", "test@example.com").add_roles("_Test Role 3")

		role = nxenv.get_doc("Role", "_Test Role 3")
		role.disabled = 1
		role.save()

		self.assertTrue("_Test Role 3" not in nxenv.get_roles("test@example.com"))

		role = nxenv.get_doc("Role", "_Test Role 3")
		role.disabled = 0
		role.save()

		nxenv.get_doc("User", "test@example.com").add_roles("_Test Role 3")
		self.assertTrue("_Test Role 3" in nxenv.get_roles("test@example.com"))

	def test_change_desk_access(self):
		"""if we change desk acecss from role, remove from user"""
		nxenv.delete_doc_if_exists("User", "test-user-for-desk-access@example.com")
		nxenv.delete_doc_if_exists("Role", "desk-access-test")
		user = nxenv.get_doc(
			doctype="User", email="test-user-for-desk-access@example.com", first_name="test"
		).insert()
		role = nxenv.get_doc(doctype="Role", role_name="desk-access-test", desk_access=0).insert()
		user.add_roles(role.name)
		user.save()
		self.assertTrue(user.user_type == "Website User")
		role.desk_access = 1
		role.save()
		user.reload()
		self.assertTrue(user.user_type == "System User")
		role.desk_access = 0
		role.save()
		user.reload()
		self.assertTrue(user.user_type == "Website User")

	def test_get_users_by_role(self):
		role = "System Manager"
		sys_managers = get_info_based_on_role(role, field="name")

		for user in sys_managers:
			self.assertIn(role, nxenv.get_roles(user))
