# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import nxenv
from nxenv.tests import IntegrationTestCase


class TestDynamicLinks(IntegrationTestCase):
	def setUp(self):
		nxenv.db.delete("Email Unsubscribe")

	def test_delete_normal(self):
		event = nxenv.get_doc(
			{
				"doctype": "Event",
				"subject": "test-for-delete",
				"starts_on": "2014-01-01",
				"event_type": "Public",
			}
		).insert()

		unsub = nxenv.get_doc(
			{
				"doctype": "Email Unsubscribe",
				"email": "test@example.com",
				"reference_doctype": event.doctype,
				"reference_name": event.name,
			}
		).insert()

		event.delete()

		self.assertFalse(nxenv.db.exists("Email Unsubscribe", unsub.name))

	def test_delete_with_comment(self):
		event = nxenv.get_doc(
			{
				"doctype": "Event",
				"subject": "test-for-delete-1",
				"starts_on": "2014-01-01",
				"event_type": "Public",
			}
		).insert()
		event.add_comment("Comment", "test")

		self.assertTrue(
			nxenv.get_all("Comment", filters={"reference_doctype": "Event", "reference_name": event.name})
		)
		event.delete()
		self.assertFalse(
			nxenv.get_all("Comment", filters={"reference_doctype": "Event", "reference_name": event.name})
		)

	def test_custom_fields(self):
		from nxenv.utils.testutils import add_custom_field, clear_custom_fields

		add_custom_field("Event", "test_ref_doc", "Link", "DocType")
		add_custom_field("Event", "test_ref_name", "Dynamic Link", "test_ref_doc")

		unsub = nxenv.get_doc(
			{"doctype": "Email Unsubscribe", "email": "test@example.com", "global_unsubscribe": 1}
		).insert()

		event = nxenv.get_doc(
			{
				"doctype": "Event",
				"subject": "test-for-delete-2",
				"starts_on": "2014-01-01",
				"event_type": "Public",
				"test_ref_doc": unsub.doctype,
				"test_ref_name": unsub.name,
			}
		).insert()

		self.assertRaises(nxenv.LinkExistsError, unsub.delete)

		event.test_ref_doc = None
		event.test_ref_name = None
		event.save()

		unsub.delete()

		clear_custom_fields("Event")
		nxenv.db.commit()  # undo changes done by DDL
