import nxenv
from nxenv import format
from nxenv.tests import IntegrationTestCase


class TestFormatter(IntegrationTestCase):
	def test_currency_formatting(self):
		df = nxenv._dict({"fieldname": "amount", "fieldtype": "Currency", "options": "currency"})

		doc = nxenv._dict({"amount": 5})
		nxenv.db.set_default("currency", "INR")

		# if currency field is not passed then default currency should be used.
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "₹ 100,000.00")

		doc.currency = "USD"
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "$ 100,000.00")

		nxenv.db.set_default("currency", None)
