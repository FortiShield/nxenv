import nxenv
import nxenv.share


def execute():
	for user in nxenv.STANDARD_USERS:
		nxenv.share.remove("User", user, user)
