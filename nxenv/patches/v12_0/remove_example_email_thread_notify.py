import nxenv


def execute():
	# remove all example.com email user accounts from notifications
	nxenv.db.sql(
		"""UPDATE `tabUser`
	SET thread_notify=0, send_me_a_copy=0
	WHERE email like '%@example.com'"""
	)
