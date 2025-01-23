import nxenv


def execute():
	nxenv.db.delete("DocType", {"name": "Feedback Request"})
