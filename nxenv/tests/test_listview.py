# Copyright (c) 2019, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import json

import nxenv
from nxenv.desk.listview import get_group_by_count, get_list_settings, set_list_settings
from nxenv.desk.reportview import get
from nxenv.tests import IntegrationTestCase


class TestListView(IntegrationTestCase):
	def setUp(self):
		if nxenv.db.exists("List View Settings", "DocType"):
			nxenv.delete_doc("List View Settings", "DocType")

	def test_get_list_settings_without_settings(self):
		self.assertIsNone(get_list_settings("DocType"), None)

	def test_get_list_settings_with_default_settings(self):
		nxenv.get_doc({"doctype": "List View Settings", "name": "DocType"}).insert()
		settings = get_list_settings("DocType")
		self.assertIsNotNone(settings)

		self.assertEqual(settings.disable_auto_refresh, 0)
		self.assertEqual(settings.disable_count, 0)
		self.assertEqual(settings.disable_comment_count, 0)
		self.assertEqual(settings.disable_sidebar_stats, 0)

	def test_get_list_settings_with_non_default_settings(self):
		nxenv.get_doc({"doctype": "List View Settings", "name": "DocType", "disable_count": 1}).insert()
		settings = get_list_settings("DocType")
		self.assertIsNotNone(settings)

		self.assertEqual(settings.disable_auto_refresh, 0)
		self.assertEqual(settings.disable_count, 1)
		self.assertEqual(settings.disable_comment_count, 0)
		self.assertEqual(settings.disable_sidebar_stats, 0)

	def test_set_list_settings_without_settings(self):
		set_list_settings("DocType", json.dumps({}))
		settings = nxenv.get_doc("List View Settings", "DocType")

		self.assertEqual(settings.disable_auto_refresh, 0)
		self.assertEqual(settings.disable_count, 0)
		self.assertEqual(settings.disable_comment_count, 0)
		self.assertEqual(settings.disable_sidebar_stats, 0)

	def test_set_list_settings_with_existing_settings(self):
		nxenv.get_doc({"doctype": "List View Settings", "name": "DocType", "disable_count": 1}).insert()
		set_list_settings("DocType", json.dumps({"disable_count": 0, "disable_auto_refresh": 1}))
		settings = nxenv.get_doc("List View Settings", "DocType")

		self.assertEqual(settings.disable_auto_refresh, 1)
		self.assertEqual(settings.disable_count, 0)
		self.assertEqual(settings.disable_comment_count, 0)
		self.assertEqual(settings.disable_sidebar_stats, 0)

	def test_list_view_child_table_filter_with_created_by_filter(self):
		if nxenv.db.exists("Note", "Test created by filter with child table filter"):
			nxenv.delete_doc("Note", "Test created by filter with child table filter")

		doc = nxenv.get_doc(
			{"doctype": "Note", "title": "Test created by filter with child table filter", "public": 1}
		)
		doc.append("seen_by", {"user": "Administrator"})
		doc.insert()

		data = {
			d.name: d.count
			for d in get_group_by_count("Note", '[["Note Seen By","user","=","Administrator"]]', "owner")
		}
		self.assertEqual(data["Administrator"], 1)

	def test_get_group_by_invalid_field(self):
		self.assertRaises(
			ValueError,
			get_group_by_count,
			"Note",
			'[["Note Seen By","user","=","Administrator"]]',
			"invalid_field",
		)

	def test_list_view_comment_count(self):
		nxenv.form_dict.doctype = "DocType"
		nxenv.form_dict.limit = "1"
		nxenv.form_dict.fields = [
			"`tabDocType`.`name`",
		]

		for with_comment_count in (1, True, "1"):
			nxenv.form_dict.with_comment_count = with_comment_count
			self.assertEqual(len(get()["values"][0]), 2)

		for with_comment_count in (0, False, "0", None):
			nxenv.form_dict.with_comment_count = with_comment_count
			self.assertEqual(len(get()["values"][0]), 1)
