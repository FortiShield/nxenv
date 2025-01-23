import json

import nxenv


def execute():
	"""Handle introduction of UI tours"""
	completed = {}
	for tour in nxenv.get_all("Form Tour", {"ui_tour": 1}, pluck="name"):
		completed[tour] = {"is_complete": True}

	User = nxenv.qb.DocType("User")
	nxenv.qb.update(User).set("onboarding_status", json.dumps(completed)).run()
