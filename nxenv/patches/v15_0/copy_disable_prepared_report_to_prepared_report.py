import nxenv


def execute():
	table = nxenv.qb.DocType("Report")
	nxenv.qb.update(table).set(table.prepared_report, 0).where(table.disable_prepared_report == 1)
