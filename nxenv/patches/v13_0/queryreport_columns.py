# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json

import nxenv


def execute():
	"""Convert Query Report json to support other content."""
	records = nxenv.get_all("Report", filters={"json": ["!=", ""]}, fields=["name", "json"])
	for record in records:
		jstr = record["json"]
		data = json.loads(jstr)
		if isinstance(data, list):
			# double escape braces
			jstr = f'{{"columns":{jstr}}}'
			nxenv.db.set_value("Report", record["name"], "json", jstr)
