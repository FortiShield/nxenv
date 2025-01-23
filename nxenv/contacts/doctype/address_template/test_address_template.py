# Copyright (c) 2015, Nxenv Technologies and Contributors
# License: MIT. See LICENSE
import nxenv
from nxenv.contacts.doctype.address_template.address_template import get_default_address_template
from nxenv.tests import IntegrationTestCase, UnitTestCase
from nxenv.utils.jinja import validate_template


class UnitTestAddressTemplate(UnitTestCase):
	"""
	Unit tests for AddressTemplate.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestAddressTemplate(IntegrationTestCase):
	def setUp(self) -> None:
		nxenv.db.delete("Address Template", {"country": "India"})
		nxenv.db.delete("Address Template", {"country": "Brazil"})

	def test_default_address_template(self):
		validate_template(get_default_address_template())

	def test_default_is_unset(self):
		nxenv.get_doc({"doctype": "Address Template", "country": "India", "is_default": 1}).insert()

		self.assertEqual(nxenv.db.get_value("Address Template", "India", "is_default"), 1)

		nxenv.get_doc({"doctype": "Address Template", "country": "Brazil", "is_default": 1}).insert()

		self.assertEqual(nxenv.db.get_value("Address Template", "India", "is_default"), 0)
		self.assertEqual(nxenv.db.get_value("Address Template", "Brazil", "is_default"), 1)

	def test_delete_address_template(self):
		india = nxenv.get_doc({"doctype": "Address Template", "country": "India", "is_default": 0}).insert()

		brazil = nxenv.get_doc(
			{"doctype": "Address Template", "country": "Brazil", "is_default": 1}
		).insert()

		india.reload()  # might have been modified by the second template
		india.delete()  # should not raise an error

		self.assertRaises(nxenv.ValidationError, brazil.delete)
