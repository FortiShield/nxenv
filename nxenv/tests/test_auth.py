# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import datetime
import time

import requests
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

import nxenv
from nxenv.auth import LoginAttemptTracker
from nxenv.nxenvclient import AuthError, NxenvClient
from nxenv.sessions import Session, get_expired_sessions, get_expiry_in_seconds
from nxenv.tests import IntegrationTestCase, UnitTestCase
from nxenv.tests.test_api import NxenvAPITestCase
from nxenv.utils import get_datetime, get_site_url, now
from nxenv.utils.data import add_to_date
from nxenv.www.login import _generate_temporary_login_link


def add_user(email, password, username=None, mobile_no=None):
	first_name = email.split("@", 1)[0]
	user = nxenv.get_doc(
		doctype="User", email=email, first_name=first_name, username=username, mobile_no=mobile_no
	).insert()
	user.new_password = password
	user.simultaneous_sessions = 1
	user.add_roles("System Manager")
	nxenv.db.commit()


class TestAuth(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.HOST_NAME = nxenv.get_site_config().host_name or get_site_url(nxenv.local.site)
		cls.test_user_email = "test_auth@test.com"
		cls.test_user_name = "test_auth_user"
		cls.test_user_mobile = "+911234567890"
		cls.test_user_password = "pwd_012"

		cls.tearDownClass()
		add_user(
			email=cls.test_user_email,
			password=cls.test_user_password,
			username=cls.test_user_name,
			mobile_no=cls.test_user_mobile,
		)

	@classmethod
	def tearDownClass(cls):
		nxenv.delete_doc("User", cls.test_user_email, force=True)
		nxenv.local.request_ip = None
		nxenv.form_dict.email = None
		nxenv.local.response["http_status_code"] = None

	def set_system_settings(self, k, v):
		nxenv.db.set_single_value("System Settings", k, v)
		nxenv.clear_cache()
		nxenv.db.commit()

	def test_allow_login_using_mobile(self):
		self.set_system_settings("allow_login_using_mobile_number", 1)
		self.set_system_settings("allow_login_using_user_name", 0)

		# Login by both email and mobile should work
		NxenvClient(self.HOST_NAME, self.test_user_mobile, self.test_user_password)
		NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password)

		# login by username should fail
		with self.assertRaises(AuthError):
			NxenvClient(self.HOST_NAME, self.test_user_name, self.test_user_password)

	def test_allow_login_using_only_email(self):
		self.set_system_settings("allow_login_using_mobile_number", 0)
		self.set_system_settings("allow_login_using_user_name", 0)

		# Login by mobile number should fail
		with self.assertRaises(AuthError):
			NxenvClient(self.HOST_NAME, self.test_user_mobile, self.test_user_password)

		# login by username should fail
		with self.assertRaises(AuthError):
			NxenvClient(self.HOST_NAME, self.test_user_name, self.test_user_password)

		# Login by email should work
		NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password)

	def test_allow_login_using_username(self):
		self.set_system_settings("allow_login_using_mobile_number", 0)
		self.set_system_settings("allow_login_using_user_name", 1)

		# Mobile login should fail
		with self.assertRaises(AuthError):
			NxenvClient(self.HOST_NAME, self.test_user_mobile, self.test_user_password)

		# Both email and username logins should work
		NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password)
		NxenvClient(self.HOST_NAME, self.test_user_name, self.test_user_password)

	def test_allow_login_using_username_and_mobile(self):
		self.set_system_settings("allow_login_using_mobile_number", 1)
		self.set_system_settings("allow_login_using_user_name", 1)

		# Both email and username and mobile logins should work
		NxenvClient(self.HOST_NAME, self.test_user_mobile, self.test_user_password)
		NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password)
		NxenvClient(self.HOST_NAME, self.test_user_name, self.test_user_password)

	def test_deny_multiple_login(self):
		self.set_system_settings("deny_multiple_sessions", 1)
		self.addCleanup(self.set_system_settings, "deny_multiple_sessions", 0)

		first_login = NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password)
		first_login.get_list("ToDo")

		second_login = NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password)
		second_login.get_list("ToDo")
		with self.assertRaises(Exception):
			first_login.get_list("ToDo")

		third_login = NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password)
		with self.assertRaises(Exception):
			first_login.get_list("ToDo")
		with self.assertRaises(Exception):
			second_login.get_list("ToDo")
		third_login.get_list("ToDo")

	def test_disable_user_pass_login(self):
		NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password).get_list("ToDo")
		self.set_system_settings("disable_user_pass_login", 1)
		self.addCleanup(self.set_system_settings, "disable_user_pass_login", 0)

		with self.assertRaises(Exception):
			NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password).get_list("ToDo")

	def test_login_with_email_link(self):
		user = self.test_user_email

		# Logs in
		res = requests.get(_generate_temporary_login_link(user, 10))
		self.assertEqual(res.status_code, 200)
		self.assertTrue(res.cookies.get("sid"))
		self.assertNotEqual(res.cookies.get("sid"), "Guest")

		# Random incorrect URL
		res = requests.get(_generate_temporary_login_link(user, 10) + "aa")
		self.assertEqual(res.cookies.get("sid"), "Guest")

		# POST doesn't work
		res = requests.post(_generate_temporary_login_link(user, 10))
		self.assertEqual(res.status_code, 403)

		# Rate limiting
		for _ in range(6):
			res = requests.get(_generate_temporary_login_link(user, 10))
			if res.status_code == 429:
				break
		else:
			self.fail("Rate limting not working")

	def test_correct_cookie_expiry_set(self):
		client = NxenvClient(self.HOST_NAME, self.test_user_email, self.test_user_password)

		expiry_time = next(x for x in client.session.cookies if x.name == "sid").expires
		current_time = datetime.datetime.now(tz=datetime.UTC).timestamp()
		self.assertAlmostEqual(get_expiry_in_seconds(), expiry_time - current_time, delta=60 * 60)


class TestAllowedReferrer(UnitTestCase):
	def test_is_allowed_referrer(self):
		def create_request(headers):
			builder = EnvironBuilder(headers=headers)
			env = builder.get_environ()
			return Request(env)

		# Test with valid referrer
		nxenv.cache.set_value("allowed_referrers", ["https://example.com"])
		nxenv.local.request = create_request({"Referer": "https://example.com/some/path"})
		http_request = nxenv.auth.HTTPRequest()
		self.assertTrue(http_request.is_allowed_referrer())

		# Test with invalid referrer
		nxenv.local.request = create_request({"Referer": "https://malicious.com"})
		http_request = nxenv.auth.HTTPRequest()
		self.assertFalse(http_request.is_allowed_referrer())

		# Test with valid origin
		nxenv.local.request = create_request({"Origin": "https://example.com"})
		http_request = nxenv.auth.HTTPRequest()
		self.assertTrue(http_request.is_allowed_referrer())

		# Test with invalid origin
		nxenv.local.request = create_request({"Origin": "https://malicious.com"})
		http_request = nxenv.auth.HTTPRequest()
		self.assertFalse(http_request.is_allowed_referrer())

		# Clean up
		nxenv.cache.delete_value("allowed_referrers")
		nxenv.local.request = None


class TestLoginAttemptTracker(IntegrationTestCase):
	def test_account_lock(self):
		"""Make sure that account locks after `n consecutive failures"""
		tracker = LoginAttemptTracker("tester", max_consecutive_login_attempts=3, lock_interval=60)
		# Clear the cache by setting attempt as success
		tracker.add_success_attempt()

		tracker.add_failure_attempt()
		self.assertTrue(tracker.is_user_allowed())

		tracker.add_failure_attempt()
		self.assertTrue(tracker.is_user_allowed())

		tracker.add_failure_attempt()
		self.assertTrue(tracker.is_user_allowed())

		tracker.add_failure_attempt()
		self.assertFalse(tracker.is_user_allowed())

	def test_account_unlock(self):
		"""Make sure that locked account gets unlocked after lock_interval of time."""
		lock_interval = 2  # In sec
		tracker = LoginAttemptTracker("tester", max_consecutive_login_attempts=1, lock_interval=lock_interval)
		# Clear the cache by setting attempt as success
		tracker.add_success_attempt()

		tracker.add_failure_attempt()
		self.assertTrue(tracker.is_user_allowed())

		tracker.add_failure_attempt()
		self.assertFalse(tracker.is_user_allowed())

		# Sleep for lock_interval of time, so that next request con unlock the user access.
		time.sleep(lock_interval)

		tracker.add_failure_attempt()
		self.assertTrue(tracker.is_user_allowed())


class TestSessionExpirty(NxenvAPITestCase):
	def test_session_expires(self):
		sid = self.sid  # triggers login for test case login
		s: Session = nxenv.local.session_obj

		expiry_in = get_expiry_in_seconds()
		session_created = now()

		# Try with 1% increments of times, it should always work
		for step in range(0, 100, 1):
			seconds_elapsed = expiry_in * step / 100

			time_now = add_to_date(session_created, seconds=seconds_elapsed, as_string=True)
			with self.freeze_time(time_now):
				data = s.get_session_data_from_db()
				self.assertEqual(data.user, "Administrator")

		# 1% higher should immediately expire
		time_of_expiry = add_to_date(session_created, seconds=expiry_in * 1.01, as_string=True)
		with self.freeze_time(time_of_expiry):
			self.assertIn(sid, get_expired_sessions())
			self.assertFalse(s.get_session_data_from_db())
