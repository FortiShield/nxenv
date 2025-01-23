import nxenv


def execute():
	if nxenv.db.db_type == "mariadb":
		nxenv.db.sql_ddl("alter table `tabSingles` modify column `value` longtext")
