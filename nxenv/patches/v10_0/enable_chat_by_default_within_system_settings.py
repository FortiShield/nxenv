import nxenv


def execute():
	nxenv.reload_doctype("System Settings")
	doc = nxenv.get_single("System Settings")
	doc.enable_chat = 1

	# Changes prescribed by Nabin Hait (nabin@nxenv.io)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_permissions = True

	doc.save()
