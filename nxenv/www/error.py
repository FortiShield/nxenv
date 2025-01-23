# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import nxenv
from nxenv import _

no_cache = 1


def get_context(context):
	if nxenv.flags.in_migrate:
		return

	allow_traceback = nxenv.get_system_settings("allow_error_traceback") if nxenv.db else False
	if nxenv.local.flags.disable_traceback and not nxenv.local.dev_server:
		allow_traceback = False

	if not context.title:
		context.title = _("Server Error")
	if not context.message:
		context.message = _("There was an error building this page")

	return {
		"error": nxenv.get_traceback().replace("<", "&lt;").replace(">", "&gt;") if allow_traceback else ""
	}
