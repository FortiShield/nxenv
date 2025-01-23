import nxenv


def execute():
	Event = nxenv.qb.DocType("Event")
	query = (
		nxenv.qb.update(Event)
		.set(Event.event_type, "Private")
		.set(Event.status, "Cancelled")
		.where(Event.event_type == "Cancelled")
	)
	query.run()
