# Copyright (c) 2019, Nxenv Technologies and Contributors
# License: MIT. See LICENSE
import nxenv
from nxenv.core.doctype.data_export.exporter import DataExporter
from nxenv.tests import IntegrationTestCase, UnitTestCase


class UnitTestDataExport(UnitTestCase):
	"""
	Unit tests for DataExport.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestDataExporter(IntegrationTestCase):
	def setUp(self):
		self.doctype_name = "Test DocType for Export Tool"
		self.doc_name = "Test Data for Export Tool"
		self.create_doctype_if_not_exists(doctype_name=self.doctype_name)
		self.create_test_data()

	def create_doctype_if_not_exists(self, doctype_name, force=False):
		"""
		Helper Function for setting up doctypes
		"""
		if force:
			nxenv.delete_doc_if_exists("DocType", doctype_name)
			nxenv.delete_doc_if_exists("DocType", "Child 1 of " + doctype_name)

		if nxenv.db.exists("DocType", doctype_name):
			return

		# Child Table 1
		table_1_name = "Child 1 of " + doctype_name
		nxenv.get_doc(
			{
				"doctype": "DocType",
				"name": table_1_name,
				"module": "Custom",
				"custom": 1,
				"istable": 1,
				"fields": [
					{"label": "Child Title", "fieldname": "child_title", "reqd": 1, "fieldtype": "Data"},
					{"label": "Child Number", "fieldname": "child_number", "fieldtype": "Int"},
				],
			}
		).insert()

		# Main Table
		nxenv.get_doc(
			{
				"doctype": "DocType",
				"name": doctype_name,
				"module": "Custom",
				"custom": 1,
				"autoname": "field:title",
				"fields": [
					{"label": "Title", "fieldname": "title", "reqd": 1, "fieldtype": "Data"},
					{"label": "Number", "fieldname": "number", "fieldtype": "Int"},
					{
						"label": "Table Field 1",
						"fieldname": "table_field_1",
						"fieldtype": "Table",
						"options": table_1_name,
					},
				],
				"permissions": [{"role": "System Manager"}],
			}
		).insert()

	def create_test_data(self, force=False):
		"""
		Helper Function creating test data
		"""
		if force:
			nxenv.delete_doc(self.doctype_name, self.doc_name)

		if not nxenv.db.exists(self.doctype_name, self.doc_name):
			self.doc = nxenv.get_doc(
				doctype=self.doctype_name,
				title=self.doc_name,
				number="100",
				table_field_1=[
					{"child_title": "Child Title 1", "child_number": "50"},
					{"child_title": "Child Title 2", "child_number": "51"},
				],
			).insert()
		else:
			self.doc = nxenv.get_doc(self.doctype_name, self.doc_name)

	def test_export_content(self):
		exp = DataExporter(doctype=self.doctype_name, file_type="CSV")
		exp.build_response()

		self.assertEqual(nxenv.response["type"], "csv")
		self.assertEqual(nxenv.response["doctype"], self.doctype_name)
		self.assertTrue(nxenv.response["result"])
		self.assertRegex(nxenv.response["result"], r"Child Title 1.*?,50")
		self.assertRegex(nxenv.response["result"], r"Child Title 2.*?,51")

	def test_export_type(self):
		for type in ["csv", "Excel"]:
			with self.subTest(type=type):
				exp = DataExporter(doctype=self.doctype_name, file_type=type)
				exp.build_response()

				self.assertEqual(nxenv.response["doctype"], self.doctype_name)
				self.assertTrue(nxenv.response["result"])

				if type == "csv":
					self.assertEqual(nxenv.response["type"], "csv")
				elif type == "Excel":
					self.assertEqual(nxenv.response["type"], "binary")
					self.assertEqual(
						nxenv.response["filename"], self.doctype_name + ".xlsx"
					)  # 'Test DocType for Export Tool.xlsx')
					self.assertTrue(nxenv.response["filecontent"])

	def tearDown(self):
		pass
