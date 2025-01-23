# Copyright (c) 2022, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.tests import IntegrationTestCase
from nxenv.tests.utils import make_test_objects
from nxenv.utils import format_date, today
from nxenv.utils.goal import get_monthly_goal_graph_data, get_monthly_results


class TestGoal(IntegrationTestCase):
	def setUp(self):
		make_test_objects("Event", reset=True)

	def tearDown(self):
		nxenv.db.delete("Event")

	def test_get_monthly_results(self):
		"""Test monthly aggregation values of a field"""
		result_dict = get_monthly_results(
			"Event",
			"subject",
			"creation",
			filters={"event_type": "Private"},
			aggregation="count",
		)

		self.assertEqual(result_dict.get(format_date(today(), "MM-yyyy")), 2)

	def test_get_monthly_goal_graph_data(self):
		"""Test for accurate values in graph data (based on test_get_monthly_results)"""
		docname = nxenv.get_list("Event", filters={"subject": ["=", "_Test Event 1"]})[0]["name"]
		nxenv.db.set_value("Event", docname, "description", 1)
		data = get_monthly_goal_graph_data(
			"Test",
			"Event",
			docname,
			"description",
			"description",
			"description",
			"Event",
			"",
			"description",
			"creation",
			filters={"starts_on": "2014-01-01"},
			aggregation="count",
		)
		self.assertEqual(float(data["data"]["datasets"][0]["values"][-1]), 1)
