import nxenv


def execute():
	days = nxenv.db.get_single_value("Website Settings", "auto_account_deletion")
	nxenv.db.set_single_value("Website Settings", "auto_account_deletion", days * 24)
