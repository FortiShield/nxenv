import nxenv
from nxenv.utils import cint


def execute():
	expiry_period = (
		cint(nxenv.db.get_singles_dict("System Settings").get("prepared_report_expiry_period")) or 30
	)
	nxenv.get_single("Log Settings").register_doctype("Prepared Report", expiry_period)
