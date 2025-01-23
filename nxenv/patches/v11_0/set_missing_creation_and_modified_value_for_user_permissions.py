import nxenv


def execute():
	nxenv.db.sql(
		"""UPDATE `tabUser Permission`
		SET `modified`=NOW(), `creation`=NOW()
		WHERE `creation` IS NULL"""
	)
