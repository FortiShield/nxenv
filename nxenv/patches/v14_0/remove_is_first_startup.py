import nxenv


def execute():
	singles = nxenv.qb.Table("tabSingles")
	nxenv.qb.from_(singles).delete().where(
		(singles.doctype == "System Settings") & (singles.field == "is_first_startup")
	).run()
