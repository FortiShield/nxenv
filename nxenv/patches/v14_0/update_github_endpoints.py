import json

import nxenv


def execute():
	if nxenv.db.exists("Social Login Key", "github"):
		nxenv.db.set_value(
			"Social Login Key", "github", "auth_url_data", json.dumps({"scope": "user:email"})
		)
