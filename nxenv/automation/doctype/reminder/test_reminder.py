# Copyright (c) 2023, Nxenv Technologies and Contributors
# See license.txt

import nxenv
from nxenv.automation.doctype.reminder.reminder import create_new_reminder, send_reminders
from nxenv.desk.doctype.notification_log.notification_log import get_notification_logs
from nxenv.tests import IntegrationTestCase, UnitTestCase
from nxenv.utils import add_to_date, now_datetime


class UnitTestReminder(UnitTestCase):
	"""
	Unit tests for Reminder.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestReminder(IntegrationTestCase):
	def test_reminder(self):
		description = "TEST_REMINDER"

		create_new_reminder(
			remind_at=add_to_date(now_datetime(), minutes=1, as_datetime=True, as_string=True),
			description=description,
		)

		send_reminders()

		notifications = get_notification_logs()["notification_logs"]
		self.assertIn(
			description,
			[n.subject for n in notifications],
			msg=f"Failed to find reminder notification \n{notifications}",
		)
