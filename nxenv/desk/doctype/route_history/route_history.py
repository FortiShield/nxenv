# Copyright (c) 2022, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.deferred_insert import deferred_insert as _deferred_insert
from nxenv.model.document import Document


class RouteHistory(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		route: DF.Data | None
		user: DF.Link | None
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=30):
		from nxenv.query_builder import Interval
		from nxenv.query_builder.functions import Now

		table = nxenv.qb.DocType("Route History")
		nxenv.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))


@nxenv.whitelist()
def deferred_insert(routes):
	routes = [
		{
			"user": nxenv.session.user,
			"route": route.get("route"),
			"creation": route.get("creation"),
		}
		for route in nxenv.parse_json(routes)
	]

	_deferred_insert("Route History", routes)


@nxenv.whitelist()
def frequently_visited_links():
	return nxenv.get_all(
		"Route History",
		fields=["route", "count(name) as count"],
		filters={"user": nxenv.session.user},
		group_by="route",
		order_by="count desc",
		limit=5,
	)
