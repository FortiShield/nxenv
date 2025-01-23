# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
import nxenv.www.list
from nxenv import _

no_cache = 1


def get_context(context):
	if nxenv.session.user == "Guest":
		nxenv.throw(_("You need to be logged in to access this page"), nxenv.PermissionError)

	context.current_user = nxenv.get_doc("User", nxenv.session.user)
	context.show_sidebar = False
