import nxenv
from nxenv.desk.utils import slug


def execute():
	for doctype in nxenv.get_all("DocType", ["name", "route"], dict(istable=0)):
		if not doctype.route:
			nxenv.db.set_value("DocType", doctype.name, "route", slug(doctype.name), update_modified=False)
