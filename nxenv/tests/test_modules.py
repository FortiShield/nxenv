import os
import shutil
import unittest
from contextlib import contextmanager
from pathlib import Path

import nxenv
from nxenv import scrub
from nxenv.core.doctype.doctype.test_doctype import new_doctype
from nxenv.custom.doctype.custom_field.custom_field import create_custom_field
from nxenv.custom.doctype.property_setter.property_setter import make_property_setter
from nxenv.model.meta import trim_table
from nxenv.modules import export_customizations, export_module_json, get_module_path
from nxenv.modules.utils import export_doc, sync_customizations
from nxenv.tests import IntegrationTestCase
from nxenv.utils import now_datetime


def write_file(path, content):
	with open(path, "w") as f:
		f.write(content)


def delete_file(path):
	if path:
		os.remove(path)


def delete_path(path):
	if path:
		shutil.rmtree(path, ignore_errors=True)


class TestUtils(IntegrationTestCase):
	def setUp(self):
		self._dev_mode = nxenv.local.conf.developer_mode
		nxenv.local.conf.developer_mode = True

	def tearDown(self):
		nxenv.db.rollback()
		nxenv.local.conf.developer_mode = self._dev_mode
		nxenv.local.flags.pop("in_import", None)

	def test_export_module_json_no_export(self):
		nxenv.local.flags.in_import = True
		doc = nxenv.get_last_doc("DocType")
		self.assertIsNone(export_module_json(doc=doc, is_standard=True, module=doc.module))

	@unittest.skipUnless(
		os.access(nxenv.get_app_path("nxenv"), os.W_OK), "Only run if nxenv app paths is writable"
	)
	def test_export_module_json(self):
		doc = nxenv.get_last_doc("DocType", {"issingle": 0, "custom": 0})
		export_doc_path = os.path.join(
			get_module_path(doc.module),
			scrub(doc.doctype),
			scrub(doc.name),
			f"{scrub(doc.name)}.json",
		)
		with open(export_doc_path) as f:
			export_doc_before = nxenv.parse_json(f.read())

		last_modified_before = os.path.getmtime(export_doc_path)
		self.addCleanup(write_file, path=export_doc_path, content=nxenv.as_json(export_doc_before))

		nxenv.flags.in_import = False
		nxenv.conf.developer_mode = True
		export_path = export_module_json(doc=doc, is_standard=True, module=doc.module)

		last_modified_after = os.path.getmtime(export_doc_path)

		with open(f"{export_path}.json") as f:
			nxenv.parse_json(f.read())  # export_doc_after

		self.assertTrue(last_modified_after > last_modified_before)

	@unittest.skipUnless(
		os.access(nxenv.get_app_path("nxenv"), os.W_OK), "Only run if nxenv app paths is writable"
	)
	def test_export_customizations(self):
		with note_customizations():
			file_path = export_customizations(module="Custom", doctype="Note")
			self.addCleanup(delete_file, path=file_path)
			self.assertTrue(file_path.endswith("/custom/custom/note.json"))
			self.assertTrue(os.path.exists(file_path))

	@unittest.skipUnless(
		os.access(nxenv.get_app_path("nxenv"), os.W_OK), "Only run if nxenv app paths is writable"
	)
	def test_sync_customizations(self):
		with note_customizations() as (custom_field, property_setter):
			file_path = export_customizations(module="Custom", doctype="Note", sync_on_migrate=True)
			custom_field.db_set("modified", now_datetime())
			custom_field.reload()

			# Untracked property setter
			custom_prop_setter = make_property_setter(
				"Note", fieldname="content", property="bold", value="1", property_type="Check"
			)

			self.assertTrue(file_path.endswith("/custom/custom/note.json"))
			self.assertTrue(os.path.exists(file_path))
			last_modified_before = custom_field.modified

			sync_customizations(app="nxenv")
			self.assertTrue(property_setter.doctype, property_setter.name)
			self.assertTrue(custom_prop_setter.doctype, custom_prop_setter.name)

			self.assertTrue(file_path.endswith("/custom/custom/note.json"))
			self.assertTrue(os.path.exists(file_path))
			custom_field.reload()
			last_modified_after = custom_field.modified

			self.assertNotEqual(last_modified_after, last_modified_before)
			self.addCleanup(delete_file, path=file_path)

	def test_reload_doc(self):
		nxenv.db.set_value("DocType", "Note", "migration_hash", "", update_modified=False)
		self.assertFalse(nxenv.db.get_value("DocType", "Note", "migration_hash"))
		nxenv.db.set_value(
			"DocField",
			{"parent": "Note", "fieldname": "title"},
			"fieldtype",
			"Text",
			update_modified=False,
		)
		self.assertEqual(
			nxenv.db.get_value("DocField", {"parent": "Note", "fieldname": "title"}, "fieldtype"),
			"Text",
		)
		nxenv.reload_doctype("Note")
		self.assertEqual(
			nxenv.db.get_value("DocField", {"parent": "Note", "fieldname": "title"}, "fieldtype"),
			"Data",
		)
		self.assertTrue(nxenv.db.get_value("DocType", "Note", "migration_hash"))

	@unittest.skipUnless(
		os.access(nxenv.get_app_path("nxenv"), os.W_OK), "Only run if nxenv app paths is writable"
	)
	def test_export_doc(self):
		note = nxenv.new_doc("Note")
		note.title = nxenv.generate_hash(length=10)
		note.save()
		export_doc(doctype="Note", name=note.name)
		exported_doc_path = Path(
			nxenv.get_app_path("nxenv", "desk", "note", note.name, f"{note.name}.json")
		)
		self.assertTrue(os.path.exists(exported_doc_path))
		self.addCleanup(delete_path, path=exported_doc_path.parent.parent)

	@unittest.skipUnless(
		os.access(nxenv.get_app_path("nxenv"), os.W_OK), "Only run if nxenv app paths is writable"
	)
	def test_make_boilerplate(self):
		with temp_doctype() as doctype:
			scrubbed = nxenv.scrub(doctype.name)
			path = nxenv.get_app_path("nxenv", "core", "doctype", scrubbed, f"{scrubbed}.json")
			self.assertFalse(os.path.exists(path))
			doctype.custom = False
			doctype.save()
			self.assertTrue(os.path.exists(path))


@contextmanager
def temp_doctype():
	try:
		doctype = new_doctype().insert()
		yield doctype
	finally:
		doctype.delete(force=True)
		nxenv.db.sql_ddl(f"DROP TABLE `tab{doctype.name}`")


@contextmanager
def note_customizations():
	try:
		df = {
			"fieldname": "test_export_customizations_field",
			"label": "Custom Data Field",
			"fieldtype": "Data",
		}
		custom_field = create_custom_field("Note", df=df)

		property_setter = make_property_setter(
			"Note", fieldname="content", property="bold", value="1", property_type="Check"
		)
		yield custom_field, property_setter
	finally:
		custom_field.delete()
		property_setter.delete()
		trim_table("Note", dry_run=False)
		delete_path(nxenv.get_module_path("Desk", "Note"))
