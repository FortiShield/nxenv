# Copyright (c) 2022, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import contextlib
import functools
import json
import os
from textwrap import dedent

import nxenv
import nxenv.model.sync
import nxenv.modules.patch_handler
import nxenv.translate
from nxenv.cache_manager import clear_global_cache
from nxenv.core.doctype.language.language import sync_languages
from nxenv.core.doctype.navbar_settings.navbar_settings import sync_standard_items
from nxenv.core.doctype.scheduled_job_type.scheduled_job_type import sync_jobs
from nxenv.database.schema import add_column
from nxenv.deferred_insert import save_to_db as flush_deferred_inserts
from nxenv.desk.notifications import clear_notifications
from nxenv.modules.patch_handler import PatchType
from nxenv.modules.utils import sync_customizations
from nxenv.search.website_search import build_index_for_all_routes
from nxenv.utils.connections import check_connection
from nxenv.utils.dashboard import sync_dashboards
from nxenv.utils.data import cint
from nxenv.utils.fixtures import sync_fixtures
from nxenv.website.utils import clear_website_cache

NXCLI_START_MESSAGE = dedent(
	"""
	Cannot run nxcli migrate without the services running.
	If you are running nxcli in development mode, make sure that nxcli is running:

	$ nxcli start

	Otherwise, check the server logs and ensure that all the required services are running.
	"""
)


def atomic(method):
	@functools.wraps(method)
	def wrapper(*args, **kwargs):
		try:
			ret = method(*args, **kwargs)
			nxenv.db.commit()
			return ret
		except Exception as e:
			# database itself can be gone while attempting rollback.
			# We should preserve original exception in this case.
			with contextlib.suppress(Exception):
				nxenv.db.rollback()
			raise e

	return wrapper


class SiteMigration:
	"""Migrate all apps to the current version, will:
	- run before migrate hooks
	- run patches
	- sync doctypes (schema)
	- sync dashboards
	- sync jobs
	- sync fixtures
	- sync customizations
	- sync languages
	- sync web pages (from /www)
	- run after migrate hooks
	"""

	def __init__(self, skip_failing: bool = False, skip_search_index: bool = False) -> None:
		self.skip_failing = skip_failing
		self.skip_search_index = skip_search_index

	def setUp(self):
		"""Complete setup required for site migration"""
		nxenv.flags.touched_tables = set()
		self.touched_tables_file = nxenv.get_site_path("touched_tables.json")
		nxenv.clear_cache()
		add_column(doctype="DocType", column_name="migration_hash", fieldtype="Data")
		clear_global_cache()

		if os.path.exists(self.touched_tables_file):
			os.remove(self.touched_tables_file)

		self.lower_lock_timeout()
		with contextlib.suppress(Exception):
			self.kill_idle_connections()
		nxenv.flags.in_migrate = True

	def tearDown(self):
		"""Run operations that should be run post schema updation processes
		This should be executed irrespective of outcome
		"""
		nxenv.translate.clear_cache()
		clear_website_cache()
		clear_notifications()

		with open(self.touched_tables_file, "w") as f:
			json.dump(list(nxenv.flags.touched_tables), f, sort_keys=True, indent=4)

		if not self.skip_search_index:
			print(f"Queued rebuilding of search index for {nxenv.local.site}")
			nxenv.enqueue(build_index_for_all_routes, queue="long")

		nxenv.publish_realtime("version-update")
		nxenv.flags.touched_tables.clear()
		nxenv.flags.in_migrate = False

	@atomic
	def pre_schema_updates(self):
		"""Executes `before_migrate` hooks"""
		for app in nxenv.get_installed_apps():
			for fn in nxenv.get_hooks("before_migrate", app_name=app):
				nxenv.get_attr(fn)()

	@atomic
	def run_schema_updates(self):
		"""Run patches as defined in patches.txt, sync schema changes as defined in the {doctype}.json files"""
		nxenv.modules.patch_handler.run_all(
			skip_failing=self.skip_failing, patch_type=PatchType.pre_model_sync
		)
		nxenv.model.sync.sync_all()
		nxenv.modules.patch_handler.run_all(
			skip_failing=self.skip_failing, patch_type=PatchType.post_model_sync
		)

	@atomic
	def post_schema_updates(self):
		"""Execute pending migration tasks post patches execution & schema sync
		This includes:
		* Sync `Scheduled Job Type` and scheduler events defined in hooks
		* Sync fixtures & custom scripts
		* Sync in-Desk Module Dashboards
		* Sync customizations: Custom Fields, Property Setters, Custom Permissions
		* Sync Nxenv's internal language master
		* Flush deferred inserts made during maintenance mode.
		* Sync Portal Menu Items
		* Sync Installed Applications Version History
		* Execute `after_migrate` hooks
		"""
		print("Syncing jobs...")
		sync_jobs()

		print("Syncing fixtures...")
		sync_fixtures()
		sync_standard_items()

		print("Syncing dashboards...")
		sync_dashboards()

		print("Syncing customizations...")
		sync_customizations()

		print("Syncing languages...")
		sync_languages()

		print("Flushing deferred inserts...")
		flush_deferred_inserts()

		print("Removing orphan doctypes...")
		nxenv.model.sync.remove_orphan_doctypes()

		print("Syncing portal menu...")
		nxenv.get_single("Portal Settings").sync_menu()

		print("Updating installed applications...")
		nxenv.get_single("Installed Applications").update_versions()

		print("Executing `after_migrate` hooks...")
		for app in nxenv.get_installed_apps():
			for fn in nxenv.get_hooks("after_migrate", app_name=app):
				nxenv.get_attr(fn)()

	def required_services_running(self) -> bool:
		"""Return True if all required services are running. Return False and print
		instructions to stdout when required services are not available.
		"""
		service_status = check_connection(redis_services=["redis_cache"])
		are_services_running = all(service_status.values())

		if not are_services_running:
			for service in service_status:
				if not service_status.get(service, True):
					print(f"Service {service} is not running.")
			print(NXCLI_START_MESSAGE)

		return are_services_running

	def lower_lock_timeout(self):
		"""Lower timeout for table metadata locks, default is 1 day, reduce it to 5 minutes.

		This is required to avoid indefinitely waiting for metadata lock.
		"""
		if nxenv.db.db_type != "mariadb":
			return
		nxenv.db.sql("set session lock_wait_timeout = %s", 5 * 60)

	def kill_idle_connections(self, idle_limit=30):
		"""Assuming migrate has highest priority, kill everything else.

		If someone has connected to mariadb using DB console or ipython console and then acquired
		certain locks we won't be able to migrate."""
		if nxenv.db.db_type != "mariadb":
			return

		processes = nxenv.db.sql("show full processlist", as_dict=1)
		connection_id = nxenv.db.sql("select connection_id()")[0][0]
		for process in processes:
			sleeping = process.get("Command") == "Sleep"
			sleeping_since = cint(process.get("Time")) or 0
			pid = process.get("Id")

			if (
				pid
				and pid != connection_id
				and process.db == nxenv.conf.db_name
				and sleeping
				and sleeping_since > idle_limit
			):
				try:
					nxenv.db.sql(f"kill {pid}")
					print(f"Killed inactive database connection with PID {pid}")
				except Exception as e:
					# We might not have permission to do this.
					print(f"Failed to kill inactive database connection with PID {pid}: {e}")

	def run(self, site: str):
		"""Run Migrate operation on site specified. This method initializes
		and destroys connections to the site database.
		"""
		from nxenv.utils.synchronization import filelock

		if site:
			nxenv.init(site)
			nxenv.connect()

		if not self.required_services_running():
			raise SystemExit(1)

		with filelock("nxcli_migrate", timeout=1):
			self.setUp()
			try:
				self.pre_schema_updates()
				self.run_schema_updates()
				self.post_schema_updates()
			finally:
				self.tearDown()
				nxenv.destroy()
