# Copyright (c) 2024, Nxenv Technologies and Contributors
# See license.txt

import nxenv
from nxenv.tests import IntegrationTestCase, UnitTestCase


class UnitTestSystemHealthReport(UnitTestCase):
	"""
	Unit tests for SystemHealthReport.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestSystemHealthReport(IntegrationTestCase):
	def test_it_works(self):
		nxenv.get_doc("System Health Report")
