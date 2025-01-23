import nxenv
from nxenv.boot import get_user_pages_or_reports
from nxenv.desk.doctype.note.note import get_unseen_notes, mark_as_seen
from nxenv.tests import IntegrationTestCase


class TestBootData(IntegrationTestCase):
	def test_get_unseen_notes(self):
		nxenv.db.delete("Note")
		nxenv.db.delete("Note Seen By")
		note = nxenv.get_doc(
			{
				"doctype": "Note",
				"title": "Test Note",
				"notify_on_login": 1,
				"content": "Test Note 1",
				"public": 1,
			}
		)
		note.insert()

		nxenv.set_user("test@example.com")
		unseen_notes = [d.title for d in get_unseen_notes()]
		self.assertListEqual(unseen_notes, ["Test Note"])

		mark_as_seen(note.name)
		unseen_notes = [d.title for d in get_unseen_notes()]
		self.assertListEqual(unseen_notes, [])


class TestPermissionQueries(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.enterClassContext(cls.enable_safe_exec())
		return super().setUpClass()

	def test_get_user_pages_or_reports_with_permission_query(self):
		# Create a ToDo custom report with admin user
		nxenv.set_user("Administrator")
		nxenv.get_doc(
			{
				"doctype": "Report",
				"ref_doctype": "ToDo",
				"report_name": "Test Admin Report",
				"report_type": "Report Builder",
				"is_standard": "No",
			}
		).insert()

		# Add permission query such that each user can only see their own custom reports
		nxenv.get_doc(
			doctype="Server Script",
			name="test_report_permission_query",
			script_type="Permission Query",
			reference_doctype="Report",
			script="""conditions = f"(`tabReport`.is_standard = 'Yes' or `tabReport`.owner = '{nxenv.session.user}')"
				""",
		).insert()

		# Create a ToDo custom report with test user
		nxenv.set_user("test@example.com")
		nxenv.get_doc(
			{
				"doctype": "Report",
				"ref_doctype": "ToDo",
				"report_name": "Test User Report",
				"report_type": "Report Builder",
				"is_standard": "No",
			}
		).insert(ignore_permissions=True)

		get_user_pages_or_reports("Report")
		allowed_reports = nxenv.cache.get_value("has_role:Report", user=nxenv.session.user)

		# Test user must not see admin user's report
		self.assertNotIn("Test Admin Report", allowed_reports)
		self.assertIn("Test User Report", allowed_reports)
