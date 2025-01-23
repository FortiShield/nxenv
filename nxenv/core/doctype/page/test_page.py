# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import os
import unittest
from unittest.mock import patch

import nxenv
from nxenv.tests import IntegrationTestCase, UnitTestCase


class UnitTestPage(UnitTestCase):
	"""
	Unit tests for Page.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestPage(IntegrationTestCase):
	def test_naming(self):
		self.assertRaises(
			nxenv.NameError,
			nxenv.get_doc(doctype="Page", page_name="DocType", module="Core").insert,
		)

	@unittest.skipUnless(
		os.access(nxenv.get_app_path("nxenv"), os.W_OK), "Only run if nxenv app paths is writable"
	)
	@patch.dict(nxenv.conf, {"developer_mode": 1})
	def test_trashing(self):
		page = nxenv.new_doc("Page", page_name=nxenv.generate_hash(), module="Core").insert()

		page.delete()
		nxenv.db.commit()

		module_path = nxenv.get_module_path(page.module)
		dir_path = os.path.join(module_path, "page", nxenv.scrub(page.name))

		self.assertFalse(os.path.exists(dir_path))
