import nxenv


def execute():
	nxenv.reload_doc("core", "doctype", "user")
	nxenv.db.sql(
		"""
		UPDATE `tabUser`
		SET `home_settings` = ''
		WHERE `user_type` = 'System User'
	"""
	)
