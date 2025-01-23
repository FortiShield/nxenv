import re

import nxenv
from nxenv.query_builder import DocType


def execute():
	"""Replace temporarily available Database Aggregate APIs on nxenv (develop)

	APIs changed:
	        * nxenv.db.max => nxenv.qb.max
	        * nxenv.db.min => nxenv.qb.min
	        * nxenv.db.sum => nxenv.qb.sum
	        * nxenv.db.avg => nxenv.qb.avg
	"""
	ServerScript = DocType("Server Script")
	server_scripts = (
		nxenv.qb.from_(ServerScript)
		.where(
			ServerScript.script.like("%nxenv.db.max(%")
			| ServerScript.script.like("%nxenv.db.min(%")
			| ServerScript.script.like("%nxenv.db.sum(%")
			| ServerScript.script.like("%nxenv.db.avg(%")
		)
		.select("name", "script")
		.run(as_dict=True)
	)

	for server_script in server_scripts:
		name, script = server_script["name"], server_script["script"]

		for agg in ["avg", "max", "min", "sum"]:
			script = re.sub(f"nxenv.db.{agg}\\(", f"nxenv.qb.{agg}(", script)

		nxenv.db.set_value("Server Script", name, "script", script)
