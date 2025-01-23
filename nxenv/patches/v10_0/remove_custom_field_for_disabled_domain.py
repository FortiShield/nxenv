import nxenv


def execute():
	nxenv.reload_doc("core", "doctype", "domain")
	nxenv.reload_doc("core", "doctype", "has_domain")
	active_domains = nxenv.get_active_domains()
	all_domains = nxenv.get_all("Domain")

	for d in all_domains:
		if d.name not in active_domains:
			inactive_domain = nxenv.get_doc("Domain", d.name)
			inactive_domain.setup_data()
			inactive_domain.remove_custom_field()
