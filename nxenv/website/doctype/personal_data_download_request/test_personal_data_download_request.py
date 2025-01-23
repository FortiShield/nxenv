# Copyright (c) 2019, Nxenv Technologies and Contributors
# License: MIT. See LICENSE
import json

import nxenv
from nxenv.contacts.doctype.contact.contact import get_contact_name
from nxenv.core.doctype.user.user import create_contact
from nxenv.tests import IntegrationTestCase, UnitTestCase
from nxenv.website.doctype.personal_data_download_request.personal_data_download_request import (
	get_user_data,
)


class UnitTestPersonalDataDownloadRequest(UnitTestCase):
	"""
	Unit tests for PersonalDataDownloadRequest.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestRequestPersonalData(IntegrationTestCase):
	def setUp(self):
		create_user_if_not_exists(email="test_privacy@example.com")

	def tearDown(self):
		nxenv.db.delete("Personal Data Download Request")

	def test_user_data_creation(self):
		user_data = json.loads(get_user_data("test_privacy@example.com"))
		contact_name = get_contact_name("test_privacy@example.com")
		expected_data = {"Contact": nxenv.get_all("Contact", {"name": contact_name}, ["*"])}
		expected_data = json.loads(json.dumps(expected_data, default=str))
		self.assertEqual({"Contact": user_data["Contact"]}, expected_data)

	def test_file_and_email_creation(self):
		nxenv.set_user("test_privacy@example.com")
		download_request = nxenv.get_doc(
			{"doctype": "Personal Data Download Request", "user": "test_privacy@example.com"}
		)
		download_request.save(ignore_permissions=True)

		nxenv.set_user("Administrator")

		file_count = nxenv.db.count(
			"File",
			{
				"attached_to_doctype": "Personal Data Download Request",
				"attached_to_name": download_request.name,
			},
		)

		self.assertEqual(file_count, 1)

		email_queue = nxenv.get_all("Email Queue", fields=["message"], order_by="creation DESC", limit=1)
		self.assertIn(nxenv._("Download Your Data"), email_queue[0].message)

		nxenv.db.delete("Email Queue")


def create_user_if_not_exists(email, first_name=None):
	nxenv.delete_doc_if_exists("User", email)

	user = nxenv.get_doc(
		{
			"doctype": "User",
			"user_type": "Website User",
			"email": email,
			"send_welcome_email": 0,
			"first_name": first_name or email.split("@", 1)[0],
			"birth_date": nxenv.utils.now_datetime(),
		}
	).insert(ignore_permissions=True)
	create_contact(user=user)
