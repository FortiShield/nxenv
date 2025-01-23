# Copyright (c) 2020, Nxenv Technologies and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.core.doctype.installed_applications.installed_applications import (
	InvalidAppOrder,
	update_installed_apps_order,
)
from nxenv.tests import IntegrationTestCase, UnitTestCase


class UnitTestInstalledApplications(UnitTestCase):
	"""
	Unit tests for InstalledApplications.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestInstalledApplications(IntegrationTestCase):
	def test_order_change(self):
		update_installed_apps_order(["nxenv"])
		self.assertRaises(InvalidAppOrder, update_installed_apps_order, [])
		self.assertRaises(InvalidAppOrder, update_installed_apps_order, ["nxenv", "deepmind"])
