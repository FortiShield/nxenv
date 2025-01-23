# Copyright (c) 2020, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import json

import nxenv

# import nxenv
from nxenv.model.document import Document


class DashboardSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		chart_config: DF.Code | None
		user: DF.Link | None
	# end: auto-generated types

	pass


@nxenv.whitelist()
def create_dashboard_settings(user):
	if not nxenv.db.exists("Dashboard Settings", user):
		doc = nxenv.new_doc("Dashboard Settings")
		doc.name = user
		doc.insert(ignore_permissions=True)
		nxenv.db.commit()
		return doc


def get_permission_query_conditions(user):
	if not user:
		user = nxenv.session.user

	return f"""(`tabDashboard Settings`.name = {nxenv.db.escape(user)})"""


@nxenv.whitelist()
def save_chart_config(reset, config, chart_name):
	reset = nxenv.parse_json(reset)
	doc = nxenv.get_doc("Dashboard Settings", nxenv.session.user)
	chart_config = nxenv.parse_json(doc.chart_config) or {}

	if reset:
		chart_config[chart_name] = {}
	else:
		config = nxenv.parse_json(config)
		if chart_name not in chart_config:
			chart_config[chart_name] = {}
		chart_config[chart_name].update(config)

	nxenv.db.set_value("Dashboard Settings", nxenv.session.user, "chart_config", json.dumps(chart_config))
