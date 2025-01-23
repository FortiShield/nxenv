import nxenv


def execute():
	if nxenv.db.table_exists("Prepared Report"):
		nxenv.reload_doc("core", "doctype", "prepared_report")
		prepared_reports = nxenv.get_all("Prepared Report")
		for report in prepared_reports:
			nxenv.delete_doc("Prepared Report", report.name)
