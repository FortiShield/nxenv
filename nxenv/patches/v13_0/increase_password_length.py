import nxenv


def execute():
	nxenv.db.change_column_type("__Auth", column="password", type="TEXT")
