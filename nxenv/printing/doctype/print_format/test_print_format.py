# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import os
import re
import unittest
from typing import TYPE_CHECKING

import nxenv
from nxenv.tests import IntegrationTestCase, UnitTestCase

if TYPE_CHECKING:
	from nxenv.printing.doctype.print_format.print_format import PrintFormat


class UnitTestPrintFormat(UnitTestCase):
	"""
	Unit tests for PrintFormat.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestPrintFormat(IntegrationTestCase):
	def test_print_user(self, style=None):
		print_html = nxenv.get_print("User", "Administrator", style=style)
		self.assertTrue("<label>First Name: </label>" in print_html)
		self.assertTrue(re.findall(r'<div class="col-xs-[^"]*">[\s]*administrator[\s]*</div>', print_html))
		return print_html

	def test_print_user_standard(self):
		print_html = self.test_print_user("Standard")
		self.assertTrue(re.findall(r"\.print-format {[\s]*font-size: 9pt;", print_html))
		self.assertFalse(re.findall(r"th {[\s]*background-color: #eee;[\s]*}", print_html))
		self.assertFalse("font-family: serif;" in print_html)

	def test_print_user_modern(self):
		print_html = self.test_print_user("Modern")
		self.assertTrue("/* modern format: for-test */" in print_html)

	def test_print_user_classic(self):
		print_html = self.test_print_user("Classic")
		self.assertTrue("/* classic format: for-test */" in print_html)

	@unittest.skipUnless(
		os.access(nxenv.get_app_path("nxenv"), os.W_OK), "Only run if nxenv app paths is writable"
	)
	def test_export_doc(self):
		doc: PrintFormat = nxenv.get_doc("Print Format", self.globalTestRecords["Print Format"][0]["name"])

		# this is only to make export_doc happy
		doc.standard = "Yes"
		_before = nxenv.conf.developer_mode
		nxenv.conf.developer_mode = True
		export_path = doc.export_doc()
		nxenv.conf.developer_mode = _before

		exported_doc_path = f"{export_path}.json"
		doc.reload()
		doc_dict = doc.as_dict(no_nulls=True, convert_dates_to_str=True)

		self.assertTrue(os.path.exists(exported_doc_path))

		with open(exported_doc_path) as f:
			exported_doc = nxenv.parse_json(f.read())

		for key, value in exported_doc.items():
			if key in doc_dict:
				with self.subTest(key=key):
					self.assertEqual(value, doc_dict[key])

		self.addCleanup(os.remove, exported_doc_path)
