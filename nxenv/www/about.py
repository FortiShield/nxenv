# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv

sitemap = 1


def get_context(context):
	context.doc = nxenv.get_cached_doc("About Us Settings")

	return context
