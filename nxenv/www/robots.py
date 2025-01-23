import nxenv

base_template_path = "www/robots.txt"


def get_context(context):
	robots_txt = (
		nxenv.db.get_single_value("Website Settings", "robots_txt")
		or (nxenv.local.conf.robots_txt and nxenv.read_file(nxenv.local.conf.robots_txt))
		or ""
	)

	return {"robots_txt": robots_txt}
