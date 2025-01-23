# Copyright (c) 2015, Nxenv Technologies and Contributors
# License: MIT. See LICENSE
import time

import nxenv
from nxenv.auth import CookieManager, LoginManager
from nxenv.tests import IntegrationTestCase, UnitTestCase


class UnitTestActivityLog(UnitTestCase):
	"""
	Unit tests for ActivityLog.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestActivityLog(IntegrationTestCase):
	def setUp(self) -> None:
		nxenv.set_user("Administrator")

	def test_activity_log(self):
		# test user login log
		nxenv.local.form_dict = nxenv._dict(
			{
				"cmd": "login",
				"sid": "Guest",
				"pwd": self.ADMIN_PASSWORD or "admin",
				"usr": "Administrator",
			}
		)

		nxenv.local.request_ip = "127.0.0.1"
		nxenv.local.cookie_manager = CookieManager()
		nxenv.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertFalse(nxenv.form_dict.pwd)
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		nxenv.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		nxenv.form_dict.update({"pwd": "password"})
		self.assertRaises(nxenv.AuthenticationError, LoginManager)
		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Failed")

		nxenv.local.form_dict = nxenv._dict()

	def get_auth_log(self, operation="Login"):
		names = nxenv.get_all(
			"Activity Log",
			filters={
				"user": "Administrator",
				"operation": operation,
			},
			order_by="`creation` DESC",
		)

		name = names[0]
		return nxenv.get_doc("Activity Log", name)

	def test_brute_security(self):
		update_system_settings({"allow_consecutive_login_attempts": 3, "allow_login_after_fail": 5})

		nxenv.local.form_dict = nxenv._dict(
			{"cmd": "login", "sid": "Guest", "pwd": self.ADMIN_PASSWORD, "usr": "Administrator"}
		)

		nxenv.local.request_ip = "127.0.0.1"
		nxenv.local.cookie_manager = CookieManager()
		nxenv.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		nxenv.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		nxenv.form_dict.update({"pwd": "password"})
		self.assertRaises(nxenv.AuthenticationError, LoginManager)
		self.assertRaises(nxenv.AuthenticationError, LoginManager)
		self.assertRaises(nxenv.AuthenticationError, LoginManager)

		# REMOVE ME: current logic allows allow_consecutive_login_attempts+1 attempts
		# before raising security exception, remove below line when that is fixed.
		self.assertRaises(nxenv.AuthenticationError, LoginManager)
		self.assertRaises(nxenv.SecurityException, LoginManager)
		time.sleep(5)
		self.assertRaises(nxenv.AuthenticationError, LoginManager)

		nxenv.local.form_dict = nxenv._dict()


def update_system_settings(args):
	doc = nxenv.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()
