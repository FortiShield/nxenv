# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.search.full_text_search import FullTextSearch
from nxenv.search.website_search import WebsiteSearch
from nxenv.utils import cint


@nxenv.whitelist(allow_guest=True)
def web_search(query, scope=None, limit=20):
	limit = cint(limit)
	ws = WebsiteSearch(index_name="web_routes")
	return ws.search(query, scope, limit)
