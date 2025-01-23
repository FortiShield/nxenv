# Copyright (c) 2018, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv

common_default_keys = ["__default", "__global"]

doctypes_for_mapping = {
	"Energy Point Rule",
	"Assignment Rule",
	"Milestone Tracker",
	"Document Naming Rule",
}


def get_doctype_map_key(doctype):
	return nxenv.scrub(doctype) + "_map"


doctype_map_keys = tuple(map(get_doctype_map_key, doctypes_for_mapping))

nxcli_cache_keys = ("assets_json",)

global_cache_keys = (
	"app_hooks",
	"installed_apps",
	"all_apps",
	"app_modules",
	"installed_app_modules",
	"module_app",
	"module_installed_app",
	"system_settings",
	"scheduler_events",
	"time_zone",
	"webhooks",
	"active_domains",
	"active_modules",
	"assignment_rule",
	"server_script_map",
	"wkhtmltopdf_version",
	"domain_restricted_doctypes",
	"domain_restricted_pages",
	"information_schema:counts",
	"db_tables",
	"server_script_autocompletion_items",
	*doctype_map_keys,
)

user_cache_keys = (
	"bootinfo",
	"user_recent",
	"roles",
	"user_doc",
	"lang",
	"defaults",
	"user_permissions",
	"home_page",
	"linked_with",
	"desktop_icons",
	"portal_menu_items",
	"user_perm_can_read",
	"has_role:Page",
	"has_role:Report",
	"desk_sidebar_items",
	"contacts",
)

doctype_cache_keys = (
	"doctype_form_meta",
	"last_modified",
	"linked_doctypes",
	"notifications",
	"workflow",
	"data_import_column_header_map",
)

wildcard_keys = (
	"document_cache::*",
	"table_columns::*",
)


def clear_user_cache(user=None):
	from nxenv.desk.notifications import clear_notifications

	# this will automatically reload the global cache
	# so it is important to clear this first
	clear_notifications(user)

	if user:
		nxenv.cache.hdel_names(user_cache_keys, user)
		nxenv.cache.delete_keys("user:" + user)
		clear_defaults_cache(user)
	else:
		nxenv.cache.delete_key(user_cache_keys)
		clear_defaults_cache()
		clear_global_cache()


def clear_domain_cache(user=None):
	domain_cache_keys = ("domain_restricted_doctypes", "domain_restricted_pages")
	nxenv.cache.delete_value(domain_cache_keys)


def clear_global_cache():
	from nxenv.website.utils import clear_website_cache

	clear_doctype_cache()
	clear_website_cache()
	nxenv.cache.delete_value(global_cache_keys + nxcli_cache_keys)
	nxenv.setup_module_map()


def clear_defaults_cache(user=None):
	if user:
		for key in [user, *common_default_keys]:
			nxenv.client_cache.delete_value(f"defaults::{key}")
	elif nxenv.flags.in_install != "nxenv":
		nxenv.client_cache.delete_keys("defaults::*")


def clear_doctype_cache(doctype=None):
	clear_controller_cache(doctype)

	_clear_doctype_cache_from_redis(doctype)
	if hasattr(nxenv.db, "after_commit"):
		nxenv.db.after_commit.add(lambda: _clear_doctype_cache_from_redis(doctype))
		nxenv.db.after_rollback.add(lambda: _clear_doctype_cache_from_redis(doctype))


def _clear_doctype_cache_from_redis(doctype: str | None = None):
	from nxenv.desk.notifications import delete_notification_count_for
	from nxenv.model.meta import clear_meta_cache

	to_del = ["is_table", "doctype_modules"]

	if doctype:

		def clear_single(dt):
			nxenv.clear_document_cache(dt)
			nxenv.cache.hdel_names(doctype_cache_keys, dt)
			clear_meta_cache(dt)

		clear_single(doctype)

		# clear all parent doctypes
		for dt in nxenv.get_all(
			"DocField", "parent", dict(fieldtype=["in", nxenv.model.table_fields], options=doctype)
		):
			clear_single(dt.parent)

		# clear all parent doctypes
		if not nxenv.flags.in_install:
			for dt in nxenv.get_all(
				"Custom Field", "dt", dict(fieldtype=["in", nxenv.model.table_fields], options=doctype)
			):
				clear_single(dt.dt)

		# clear all notifications
		delete_notification_count_for(doctype)

	else:
		# clear all
		to_del += doctype_cache_keys
		for pattern in wildcard_keys:
			to_del += nxenv.cache.get_keys(pattern)
		clear_meta_cache()

	nxenv.cache.delete_value(to_del)


def clear_controller_cache(doctype=None):
	if not doctype:
		nxenv.controllers.pop(nxenv.local.site, None)
		return

	if site_controllers := nxenv.controllers.get(nxenv.local.site):
		site_controllers.pop(doctype, None)


def get_doctype_map(doctype, name, filters=None, order_by=None):
	return nxenv.cache.hget(
		get_doctype_map_key(doctype),
		name,
		lambda: nxenv.get_all(doctype, filters=filters, order_by=order_by, ignore_ddl=True),
	)


def clear_doctype_map(doctype, name):
	nxenv.cache.hdel(nxenv.scrub(doctype) + "_map", name)


def build_table_count_cache():
	if (
		nxenv.flags.in_patch
		or nxenv.flags.in_install
		or nxenv.flags.in_migrate
		or nxenv.flags.in_import
		or nxenv.flags.in_setup_wizard
	):
		return

	table_name = nxenv.qb.Field("table_name").as_("name")
	table_rows = nxenv.qb.Field("table_rows").as_("count")
	information_schema = nxenv.qb.Schema("information_schema")

	data = (nxenv.qb.from_(information_schema.tables).select(table_name, table_rows)).run(as_dict=True)
	counts = {d.get("name").replace("tab", "", 1): d.get("count", None) for d in data}
	nxenv.cache.set_value("information_schema:counts", counts)

	return counts


def build_domain_restricted_doctype_cache(*args, **kwargs):
	if (
		nxenv.flags.in_patch
		or nxenv.flags.in_install
		or nxenv.flags.in_migrate
		or nxenv.flags.in_import
		or nxenv.flags.in_setup_wizard
	):
		return
	active_domains = nxenv.get_active_domains()
	doctypes = nxenv.get_all("DocType", filters={"restrict_to_domain": ("IN", active_domains)})
	doctypes = [doc.name for doc in doctypes]
	nxenv.cache.set_value("domain_restricted_doctypes", doctypes)

	return doctypes


def build_domain_restricted_page_cache(*args, **kwargs):
	if (
		nxenv.flags.in_patch
		or nxenv.flags.in_install
		or nxenv.flags.in_migrate
		or nxenv.flags.in_import
		or nxenv.flags.in_setup_wizard
	):
		return
	active_domains = nxenv.get_active_domains()
	pages = nxenv.get_all("Page", filters={"restrict_to_domain": ("IN", active_domains)})
	pages = [page.name for page in pages]
	nxenv.cache.set_value("domain_restricted_pages", pages)

	return pages


def clear_cache(user: str | None = None, doctype: str | None = None):
	"""Clear **User**, **DocType** or global cache.

	:param user: If user is given, only user cache is cleared.
	:param doctype: If doctype is given, only DocType cache is cleared."""
	import nxenv.cache_manager
	import nxenv.utils.caching
	from nxenv.website.router import clear_routing_cache

	if doctype:
		nxenv.cache_manager.clear_doctype_cache(doctype)
		reset_metadata_version()
	elif user:
		nxenv.cache_manager.clear_user_cache(user)
	else:  # everything
		# Delete ALL keys associated with this site.
		keys_to_delete = set(nxenv.cache.get_keys(""))
		for key in nxenv.get_hooks("persistent_cache_keys"):
			keys_to_delete.difference_update(nxenv.cache.get_keys(key))
		nxenv.cache.delete_value(list(keys_to_delete), make_keys=False)

		reset_metadata_version()
		nxenv.local.cache = {}
		nxenv.local.new_doc_templates = {}

		for fn in nxenv.get_hooks("clear_cache"):
			nxenv.get_attr(fn)()

	if (not doctype and not user) or doctype == "DocType":
		nxenv.utils.caching._SITE_CACHE.clear()
		nxenv.client_cache.clear_cache()

	nxenv.local.role_permissions = {}
	if hasattr(nxenv.local, "request_cache"):
		nxenv.local.request_cache.clear()
	if hasattr(nxenv.local, "system_settings"):
		del nxenv.local.system_settings
	if hasattr(nxenv.local, "website_settings"):
		del nxenv.local.website_settings

	clear_routing_cache()


def reset_metadata_version():
	"""Reset `metadata_version` (Client (Javascript) build ID) hash."""
	v = nxenv.generate_hash()
	nxenv.client_cache.set_value("metadata_version", v)
	return v
