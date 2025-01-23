"""
Welcome to the Deprecation Dumpster: Where Old Code Goes to Party! 🎉🗑️

This file is the final resting place (or should we say, "retirement home"?) for all the deprecated functions and methods of the Nxenv framework. It's like a code nursing home, but with more monkey-patching and less bingo.

Each function or method that checks in here comes with its own personalized decorator, complete with:
1. The date it was marked for deprecation (its "over the hill" birthday)
2. The Nxenv version at the beginning of which it becomes an error and at the end of which it will be removed (its "graduation" to the great codebase in the sky)
3. A user-facing note on alternative solutions (its "parting wisdom")

Warning: The global namespace herein is more patched up than a sailor's favorite pair of jeans. Proceed with caution and a sense of humor!

Remember, deprecated doesn't mean useless - it just means these functions are enjoying their golden years before their final bow. Treat them with respect, and maybe bring them some virtual prune juice.

Enjoy your stay in the Deprecation Dumpster, where every function gets a second chance to shine (or at least, to not break everything).
"""

import functools
import inspect
import os
import re
import sys
import typing
import warnings
from importlib.metadata import version


def colorize(text, color_code):
	if sys.stdout.isatty():
		return f"\033[{color_code}m{text}\033[0m"
	return text


class Color:
	RED = 91
	YELLOW = 93
	CYAN = 96


# we use Warning because DeprecationWarning has python default filters which would exclude them from showing
# see also nxenv.__init__ enabling them when a dev_server
class NxenvDeprecationError(Warning):
	"""Deprecated feature in current version.

	Raises an error by default but can be configured via PYTHONWARNINGS in an emergency.
	"""

	# see PYTHONWARNINGS implementation further down below


class NxenvDeprecationWarning(Warning):
	"""Deprecated feature in next version"""


class PendingNxenvDeprecationWarning(NxenvDeprecationWarning):
	"""Deprecated feature in develop beyond next version.

	Warning ignored by default.

	The deprecation decision may still be reverted or deferred at this stage.
	Regardless, using the new variant is encouraged and stable.
	"""


warnings.simplefilter("error", NxenvDeprecationError)
warnings.simplefilter("ignore", PendingNxenvDeprecationWarning)


class V15NxenvDeprecationWarning(NxenvDeprecationError):
	pass


class V16NxenvDeprecationWarning(NxenvDeprecationWarning):
	pass


class V17NxenvDeprecationWarning(PendingNxenvDeprecationWarning):
	pass


def __get_deprecation_class(graduation: str | None = None, class_name: str | None = None) -> type:
	if graduation:
		# Scrub the graduation string to ensure it's a valid class name
		cleaned_graduation = re.sub(r"\W|^(?=\d)", "_", graduation.upper())
		class_name = f"{cleaned_graduation}NxenvDeprecationWarning"
		current_module = sys.modules[__name__]
	try:
		return getattr(current_module, class_name)
	except AttributeError:
		return PendingNxenvDeprecationWarning


# Parse PYTHONWARNINGS environment variable
# see: https://github.com/python/cpython/issues/66733
pythonwarnings = os.environ.get("PYTHONWARNINGS", "")
for warning_filter in pythonwarnings.split(","):
	parts = warning_filter.strip().split(":")
	if len(parts) >= 3 and (
		parts[2] in ("NxenvDeprecationError", "NxenvDeprecationWarning", "PendingNxenvDeprecationWarning")
		or parts[2].endswith("NxenvDeprecationWarning")
	):
		try:
			# Import the warning class dynamically
			_, class_name = parts[2].rsplit(".", 1)
			warning_class = __get_deprecation_class(class_name=class_name)

			# Add the filter
			action = parts[0] if parts[0] else "default"
			message = parts[1] if len(parts) > 1 else ""
			module = parts[3] if len(parts) > 3 else ""
			lineno = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0

			warnings.filterwarnings(action, message, warning_class, module, lineno)
		except (ImportError, AttributeError):
			print(f"Warning: Unable to import {parts[2]}")


try:
	# since python 3.13, PEP 702
	from warnings import deprecated as _deprecated
except ImportError:
	import warnings
	from collections.abc import Callable
	from typing import Optional, TypeVar, Union, overload

	T = TypeVar("T", bound=Callable)

	def _deprecated(message: str, category=NxenvDeprecationWarning, stacklevel=1) -> Callable[[T], T]:
		def decorator(func: T) -> T:
			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				if message:
					warning_msg = f"{func.__name__} is deprecated.\n{message}"
				else:
					warning_msg = f"{func.__name__} is deprecated."
				warnings.warn(warning_msg, category=category, stacklevel=stacklevel + 1)
				return func(*args, **kwargs)

			return wrapper
			wrapper.__deprecated__ = True  # hint for the type checker

		return decorator


def deprecated(original: str, marked: str, graduation: str, msg: str, stacklevel: int = 1):
	"""Decorator to wrap a function/method as deprecated.

	Arguments:
	        - original: nxenv.utils.make_esc  (fully qualified)
	        - marked: 2024-09-13  (the date it has been marked)
	        - graduation: v17  (generally: current version + 2)
	"""

	def decorator(func):
		# Get the filename of the caller
		frame = inspect.currentframe()
		caller_filepath = frame.f_back.f_code.co_filename
		if os.path.basename(caller_filepath) != "deprecation_dumpster.py":
			raise RuntimeError(
				colorize("The deprecated function ", Color.YELLOW)
				+ colorize(func.__name__, Color.CYAN)
				+ colorize(" can only be called from ", Color.YELLOW)
				+ colorize("nxenv/deprecation_dumpster.py\n", Color.CYAN)
				+ colorize("Move the entire function there and import it back via adding\n ", Color.YELLOW)
				+ colorize(f"from nxenv.deprecation_dumpster import {func.__name__}\n", Color.CYAN)
				+ colorize("to file\n ", Color.YELLOW)
				+ colorize(caller_filepath, Color.CYAN)
			)

		func.__name__ = original
		wrapper = _deprecated(
			colorize(f"It was marked on {marked} for removal from {graduation} with note: ", Color.RED)
			+ colorize(f"{msg}", Color.YELLOW),
			category=__get_deprecation_class(graduation),
			stacklevel=stacklevel,
		)

		return functools.update_wrapper(wrapper, func)(func)

	return decorator


def deprecation_warning(marked: str, graduation: str, msg: str):
	"""Warn in-place from a deprecated code path, for objects use `@deprecated` decorator from the deprectation_dumpster"

	Arguments:
	        - marked: 2024-09-13  (the date it has been marked)
	        - graduation: v17  (generally: current version + 2)
	"""

	warnings.warn(
		colorize(
			f"This codepath was marked (DATE: {marked}) deprecated"
			f" for removal (from {graduation} onwards); note:\n ",
			Color.RED,
		)
		+ colorize(f"{msg}\n", Color.YELLOW),
		category=__get_deprecation_class(graduation),
		stacklevel=2,
	)


### Party starts here

if typing.TYPE_CHECKING:
	from werkzeug.local import Local


def get_local_with_deprecations() -> "Local":
	from werkzeug.local import Local

	class DeprecatedLocalAttribute:
		def __init__(self, name, warning):
			self.name = name
			self.warning = warning

		def __get__(self, obj, type=None):
			self.warning()
			return obj.__getattr__(self.name)

		def __set__(self, obj, value):
			return obj.__setattr__(self.name, value)

		def __delete__(self, obj):
			return obj.__delattr__(self.name)

	class LocalWithDeprecations(Local):
		"""Can deprecate local attributes."""

		# sites_path = DeprecatedLocalAttribute(
		# 	"sites_path",
		# 	lambda: deprecation_warning(
		# 		"2024-12-06",
		# 		"v17",
		# 		"'local.sites_path' will be deprecated: use 'nxenv.nxcli.sites.path instead'",
		# 	),
		# )

	return LocalWithDeprecations()


def _old_deprecated(func):
	return deprecated(
		"nxenv.deprecations.deprecated",
		"2024-09-13",
		"v17",
		"Make use of the nxenv/deprecation_dumpster.py file, instead. 🎉🗑️",
	)(_deprecated("")(func))


def _old_deprecation_warning(msg):
	@deprecated(
		"nxenv.deprecations.deprecation_warning",
		"2024-09-13",
		"v17",
		"Use nxenv.deprecation_dumpster.deprecation_warning, instead. 🎉🗑️",
	)
	def deprecation_warning(message, category=DeprecationWarning, stacklevel=1):
		warnings.warn(message=message, category=category, stacklevel=stacklevel + 2)

	return deprecation_warning(msg)


@deprecated("nxenv.utils.make_esc", "unknown", "v17", "Not used anymore.")
def make_esc(esc_chars):
	"""
	Function generator for Escaping special characters
	"""
	return lambda s: "".join("\\" + c if c in esc_chars else c for c in s)


@deprecated(
	"nxenv.db.is_column_missing",
	"unknown",
	"v17",
	"Renamed to nxenv.db.is_missing_column.",
)
def is_column_missing(e):
	import nxenv

	return nxenv.db.is_missing_column(e)


@deprecated(
	"nxenv.desk.doctype.bulk_update.bulk_update",
	"unknown",
	"v17",
	"Unknown.",
)
def show_progress(docnames, message, i, description):
	import nxenv

	n = len(docnames)
	nxenv.publish_progress(float(i) * 100 / n, title=message, description=description)


@deprecated(
	"nxenv.client.get_js",
	"unknown",
	"v17",
	"Unknown.",
)
def get_js(items):
	"""Load JS code files.  Will also append translations
	and extend `nxenv._messages`

	:param items: JSON list of paths of the js files to be loaded."""
	import json

	import nxenv
	from nxenv import _

	items = json.loads(items)
	out = []
	for src in items:
		src = src.strip("/").split("/")

		if ".." in src or src[0] != "assets":
			nxenv.throw(_("Invalid file path: {0}").format("/".join(src)))

		contentpath = os.path.join(nxenv.local.sites_path, *src)
		with open(contentpath) as srcfile:
			code = nxenv.utils.cstr(srcfile.read())

		out.append(code)

	return out


@deprecated(
	"nxenv.utils.print_format.read_multi_pdf",
	"unknown",
	"v17",
	"Unknown.",
)
def read_multi_pdf(output) -> bytes:
	from io import BytesIO

	with BytesIO() as merged_pdf:
		output.write(merged_pdf)
		return merged_pdf.getvalue()


@deprecated("nxenv.gzip_compress", "unknown", "v17", "Use py3 methods directly (this was compat for py2).")
def gzip_compress(data, compresslevel=9):
	"""Compress data in one shot and return the compressed string.
	Optional argument is the compression level, in range of 0-9.
	"""
	import io
	from gzip import GzipFile

	buf = io.BytesIO()
	with GzipFile(fileobj=buf, mode="wb", compresslevel=compresslevel) as f:
		f.write(data)
	return buf.getvalue()


@deprecated("nxenv.gzip_decompress", "unknown", "v17", "Use py3 methods directly (this was compat for py2).")
def gzip_decompress(data):
	"""Decompress a gzip compressed string in one shot.
	Return the decompressed string.
	"""
	import io
	from gzip import GzipFile

	with GzipFile(fileobj=io.BytesIO(data)) as f:
		return f.read()


@deprecated(
	"nxenv.email.doctype.email_queue.email_queue.send_mail",
	"unknown",
	"v17",
	"Unknown.",
)
def send_mail(email_queue_name, smtp_server_instance=None):
	"""This is equivalent to EmailQueue.send.

	This provides a way to make sending mail as a background job.
	"""
	from nxenv.email.doctype.email_queue.email_queue import EmailQueue

	record = EmailQueue.find(email_queue_name)
	record.send(smtp_server_instance=smtp_server_instance)


@deprecated(
	"nxenv.geo.country_info.get_translated_dict",
	"unknown",
	"v17",
	"Use nxenv.geo.country_info.get_translated_countries, instead.",
)
def get_translated_dict():
	from nxenv.geo.country_info import get_translated_countries

	return get_translated_countries()


@deprecated(
	"User.validate_roles",
	"unknown",
	"v17",
	"Use User.populate_role_profile_roles, instead.",
)
def validate_roles(self):
	self.populate_role_profile_roles()


@deprecated("nxenv.tests_runner.get_modules", "2024-20-08", "v17", "use nxenv.tests.utils.get_modules")
def test_runner_get_modules(doctype):
	from nxenv.tests.utils import get_modules

	return get_modules(doctype)


@deprecated(
	"nxenv.tests_runner.make_test_records", "2024-20-08", "v17", "use nxenv.tests.utils.make_test_records"
)
def test_runner_make_test_records(*args, **kwargs):
	from nxenv.tests.utils import make_test_records

	return make_test_records(*args, **kwargs)


@deprecated(
	"nxenv.tests_runner.make_test_objects", "2024-20-08", "v17", "use nxenv.tests.utils.make_test_objects"
)
def test_runner_make_test_objects(*args, **kwargs):
	from nxenv.tests.utils import make_test_objects

	return make_test_objects(*args, **kwargs)


@deprecated(
	"nxenv.tests_runner.make_test_records_for_doctype",
	"2024-20-08",
	"v17",
	"use nxenv.tests.utils.make_test_records_for_doctype",
)
def test_runner_make_test_records_for_doctype(*args, **kwargs):
	from nxenv.tests.utils import make_test_records_for_doctype

	return make_test_records_for_doctype(*args, **kwargs)


@deprecated(
	"nxenv.tests_runner.print_mandatory_fields",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_runner_print_mandatory_fields(*args, **kwargs):
	from nxenv.tests.utils.generators import print_mandatory_fields

	return print_mandatory_fields(*args, **kwargs)


@deprecated(
	"nxenv.tests_runner.get_test_record_log",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_runner_get_test_record_log(doctype):
	from nxenv.tests.utils.generators import TestRecordManager

	return TestRecordManager().get(doctype)


@deprecated(
	"nxenv.tests_runner.add_to_test_record_log",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_runner_add_to_test_record_log(doctype):
	from nxenv.tests.utils.generators import TestRecordManager

	return TestRecordManager().add(doctype)


@deprecated(
	"nxenv.tests_runner.main",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_runner_main(*args, **kwargs):
	from nxenv.commands.testing import main

	return main(*args, **kwargs)


@deprecated(
	"nxenv.tests_runner.xmlrunner_wrapper",
	"2024-20-08",
	"v17",
	"no public api anymore",
)
def test_xmlrunner_wrapper(output):
	"""Convenience wrapper to keep method signature unchanged for XMLTestRunner and TextTestRunner"""
	try:
		import xmlrunner
	except ImportError:
		print("Development dependencies are required to execute this command. To install run:")
		print("$ nxcli setup requirements --dev")
		raise

	def _runner(*args, **kwargs):
		kwargs["output"] = output
		return xmlrunner.XMLTestRunner(*args, **kwargs)

	return _runner


@deprecated(
	"nxenv.tests.upate_system_settings",
	"2024-20-08",
	"v17",
	"use with `self.change_settings(...):` context manager",
)
def tests_update_system_settings(args, commit=False):
	import nxenv

	doc = nxenv.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()
	if commit:
		# moved here
		nxenv.db.commit()  # nosemgrep


@deprecated(
	"nxenv.tests.get_system_setting",
	"2024-20-08",
	"v17",
	"use `nxenv.db.get_single_value('System Settings', key)`",
)
def tests_get_system_setting(key):
	import nxenv

	return nxenv.db.get_single_value("System Settings", key)


@deprecated(
	"nxenv.tests.utils.change_settings",
	"2024-20-08",
	"v17",
	"use `nxenv.tests.change_settings` or the cls.change_settings",
)
def tests_change_settings(*args, **kwargs):
	from nxenv.tests.classes.context_managers import change_settings

	return change_settings(*args, **kwargs)


@deprecated(
	"nxenv.tests.utils.patch_hooks",
	"2024-20-08",
	"v17",
	"use `nxenv.tests.patch_hooks` or the cls.patch_hooks",
)
def tests_patch_hooks(*args, **kwargs):
	from nxenv.tests.classes.context_managers import patch_hooks

	return patch_hooks(*args, **kwargs)


@deprecated(
	"nxenv.tests.utils.debug_on",
	"2024-20-08",
	"v17",
	"use `nxenv.tests.debug_on` or the cls.debug_on",
)
def tests_debug_on(*args, **kwargs):
	from nxenv.tests.classes.context_managers import debug_on

	return debug_on(*args, **kwargs)


@deprecated(
	"nxenv.tests.utils.timeout",
	"2024-20-08",
	"v17",
	"use `nxenv.tests.timeout` or the cls.timeout",
)
def tests_timeout(*args, **kwargs):
	from nxenv.tests.classes.context_managers import timeout

	return timeout(*args, **kwargs)


def get_tests_CompatNxenvTestCase():
	"""Unfortunately, due to circular imports, we just have to copy the entire old implementation here, even though IntegrationTestCase is overwhelmingly api-compatible."""
	import copy
	import datetime
	import unittest
	from collections.abc import Sequence
	from contextlib import contextmanager

	import nxenv
	from nxenv.model.base_document import BaseDocument
	from nxenv.utils import cint

	datetime_like_types = (datetime.datetime, datetime.date, datetime.time, datetime.timedelta)

	def _commit_watcher():
		import traceback

		print("Warning:, transaction committed during tests.")
		traceback.print_stack(limit=10)

	def _rollback_db():
		nxenv.db.value_cache = {}
		nxenv.db.rollback()

	def _restore_thread_locals(flags):
		nxenv.local.flags = flags
		nxenv.local.error_log = []
		nxenv.local.message_log = []
		nxenv.local.debug_log = []
		nxenv.local.conf = nxenv._dict(nxenv.get_site_config())
		nxenv.local.cache = {}
		nxenv.local.lang = "en"
		nxenv.local.preload_assets = {"style": [], "script": [], "icons": []}

		if hasattr(nxenv.local, "request"):
			delattr(nxenv.local, "request")

	class NxenvTestCase(unittest.TestCase):
		"""Base test class for Nxenv tests.


		If you specify `setUpClass` then make sure to call `super().setUpClass`
		otherwise this class will become ineffective.
		"""

		@deprecated(
			"nxenv.tests.utils.NxenvTestCase",
			"2024-20-08",
			"v17",
			"Import `nxenv.tests.UnitTestCase` or `nxenv.tests.IntegrationTestCase` respectively instead of `nxenv.tests.utils.NxenvTestCase` - also see wiki for more info: https://github.com/nxenv/nxenv/wiki#testing-guide",
		)
		def __new__(cls, *args, **kwargs):
			return super().__new__(cls)

		TEST_SITE = "test_site"

		SHOW_TRANSACTION_COMMIT_WARNINGS = False
		maxDiff = 10_000  # prints long diffs but useful in CI

		@classmethod
		def setUpClass(cls) -> None:
			cls.TEST_SITE = getattr(nxenv.local, "site", None) or cls.TEST_SITE
			nxenv.init(cls.TEST_SITE)
			cls.ADMIN_PASSWORD = nxenv.get_conf(cls.TEST_SITE).admin_password
			cls._primary_connection = nxenv.local.db
			cls._secondary_connection = None
			# flush changes done so far to avoid flake
			nxenv.db.commit()  # nosemgrep
			if cls.SHOW_TRANSACTION_COMMIT_WARNINGS:
				nxenv.db.before_commit.add(_commit_watcher)

			# enqueue teardown actions (executed in LIFO order)
			cls.addClassCleanup(_restore_thread_locals, copy.deepcopy(nxenv.local.flags))
			cls.addClassCleanup(_rollback_db)

			return super().setUpClass()

		def _apply_debug_decorator(self, exceptions=()):
			from nxenv.tests.utils import debug_on

			setattr(self, self._testMethodName, debug_on(*exceptions)(getattr(self, self._testMethodName)))

		def assertSequenceSubset(self, larger: Sequence, smaller: Sequence, msg=None):
			"""Assert that `expected` is a subset of `actual`."""
			self.assertTrue(set(smaller).issubset(set(larger)), msg=msg)

		# --- Nxenv Framework specific assertions
		def assertDocumentEqual(self, expected, actual):
			"""Compare a (partial) expected document with actual Document."""

			if isinstance(expected, BaseDocument):
				expected = expected.as_dict()

			for field, value in expected.items():
				if isinstance(value, list):
					actual_child_docs = actual.get(field)
					self.assertEqual(len(value), len(actual_child_docs), msg=f"{field} length should be same")
					for exp_child, actual_child in zip(value, actual_child_docs, strict=False):
						self.assertDocumentEqual(exp_child, actual_child)
				else:
					self._compare_field(value, actual.get(field), actual, field)

		def _compare_field(self, expected, actual, doc: BaseDocument, field: str):
			msg = f"{field} should be same."

			if isinstance(expected, float):
				precision = doc.precision(field)
				self.assertAlmostEqual(
					expected, actual, places=precision, msg=f"{field} should be same to {precision} digits"
				)
			elif isinstance(expected, bool | int):
				self.assertEqual(expected, cint(actual), msg=msg)
			elif isinstance(expected, datetime_like_types) or isinstance(actual, datetime_like_types):
				self.assertEqual(str(expected), str(actual), msg=msg)
			else:
				self.assertEqual(expected, actual, msg=msg)

		def normalize_html(self, code: str) -> str:
			"""Formats HTML consistently so simple string comparisons can work on them."""
			from bs4 import BeautifulSoup

			return BeautifulSoup(code, "html.parser").prettify(formatter=None)

		def normalize_sql(self, query: str) -> str:
			"""Formats SQL consistently so simple string comparisons can work on them."""
			import sqlparse

			return sqlparse.format(query.strip(), keyword_case="upper", reindent=True, strip_comments=True)

		@contextmanager
		def primary_connection(self):
			"""Switch to primary DB connection

			This is used for simulating multiple users performing actions by simulating two DB connections"""
			try:
				current_conn = nxenv.local.db
				nxenv.local.db = self._primary_connection
				yield
			finally:
				nxenv.local.db = current_conn

		@contextmanager
		def secondary_connection(self):
			"""Switch to secondary DB connection."""
			if self._secondary_connection is None:
				nxenv.connect()  # get second connection
				self._secondary_connection = nxenv.local.db

			try:
				current_conn = nxenv.local.db
				nxenv.local.db = self._secondary_connection
				yield
			finally:
				nxenv.local.db = current_conn
				self.addCleanup(self._rollback_connections)

		def _rollback_connections(self):
			self._primary_connection.rollback()
			self._secondary_connection.rollback()

		def assertQueryEqual(self, first: str, second: str):
			self.assertEqual(self.normalize_sql(first), self.normalize_sql(second))

		@contextmanager
		def assertQueryCount(self, count):
			queries = []

			def _sql_with_count(*args, **kwargs):
				ret = orig_sql(*args, **kwargs)
				queries.append(args[0].last_query)
				return ret

			try:
				orig_sql = nxenv.db.__class__.sql
				nxenv.db.__class__.sql = _sql_with_count
				yield
				self.assertLessEqual(len(queries), count, msg="Queries executed: \n" + "\n\n".join(queries))
			finally:
				nxenv.db.__class__.sql = orig_sql

		@contextmanager
		def assertRedisCallCounts(self, count):
			commands = []

			def execute_command_and_count(*args, **kwargs):
				ret = orig_execute(*args, **kwargs)
				key_len = 2
				if "H" in args[0]:
					key_len = 3
				commands.append((args)[:key_len])
				return ret

			try:
				orig_execute = nxenv.cache.execute_command
				nxenv.cache.execute_command = execute_command_and_count
				yield
				self.assertLessEqual(
					len(commands), count, msg="commands executed: \n" + "\n".join(str(c) for c in commands)
				)
			finally:
				nxenv.cache.execute_command = orig_execute

		@contextmanager
		def assertRowsRead(self, count):
			rows_read = 0

			def _sql_with_count(*args, **kwargs):
				nonlocal rows_read

				ret = orig_sql(*args, **kwargs)
				# count of last touched rows as per DB-API 2.0 https://peps.python.org/pep-0249/#rowcount
				rows_read += cint(nxenv.db._cursor.rowcount)
				return ret

			try:
				orig_sql = nxenv.db.sql
				nxenv.db.sql = _sql_with_count
				yield
				self.assertLessEqual(rows_read, count, msg="Queries read more rows than expected")
			finally:
				nxenv.db.sql = orig_sql

		@classmethod
		def enable_safe_exec(cls) -> None:
			"""Enable safe exec and disable them after test case is completed."""
			from nxenv.installer import update_site_config
			from nxenv.utils.safe_exec import SAFE_EXEC_CONFIG_KEY

			cls._common_conf = os.path.join(nxenv.local.sites_path, "common_site_config.json")
			update_site_config(SAFE_EXEC_CONFIG_KEY, 1, validate=False, site_config_path=cls._common_conf)

			cls.addClassCleanup(
				lambda: update_site_config(
					SAFE_EXEC_CONFIG_KEY, 0, validate=False, site_config_path=cls._common_conf
				)
			)

		@contextmanager
		def set_user(self, user: str):
			try:
				old_user = nxenv.session.user
				nxenv.set_user(user)
				yield
			finally:
				nxenv.set_user(old_user)

		@contextmanager
		def switch_site(self, site: str):
			"""Switch connection to different site.
			Note: Drops current site connection completely."""

			try:
				old_site = nxenv.local.site
				nxenv.init(site, force=True)
				nxenv.connect()
				yield
			finally:
				nxenv.init(old_site, force=True)
				nxenv.connect()

		@contextmanager
		def freeze_time(self, time_to_freeze, is_utc=False, *args, **kwargs):
			from zoneinfo import ZoneInfo

			from freezegun import freeze_time

			from nxenv.utils.data import convert_utc_to_timezone, get_datetime, get_system_timezone

			if not is_utc:
				# Freeze time expects UTC or tzaware objects. We have neither, so convert to UTC.
				time_to_freeze = (
					get_datetime(time_to_freeze)
					.replace(tzinfo=ZoneInfo(get_system_timezone()))
					.astimezone(ZoneInfo("UTC"))
				)

			with freeze_time(time_to_freeze, *args, **kwargs):
				yield

	return NxenvTestCase


# remove alongside get_tests_CompatNxenvTestCase
def get_compat_nxenv_test_case_preparation(cfg):
	import unittest

	import nxenv
	from nxenv.testing.environment import IntegrationTestPreparation

	class NxenvTestCasePreparation(IntegrationTestPreparation):
		def __call__(self, suite: unittest.TestSuite, app: str, category: str) -> None:
			super().__call__(suite, app, category)
			candidates = []
			app_path = nxenv.get_app_path(app)
			for path, folders, files in os.walk(nxenv.get_app_path(app)):
				for dontwalk in ("locals", ".git", "public", "__pycache__"):
					if dontwalk in folders:
						folders.remove(dontwalk)

				# for predictability
				folders.sort()
				files.sort()

				# print path
				for filename in files:
					if filename.startswith("test_") and filename.endswith(".py"):
						relative_path = os.path.relpath(path, app_path)
						if relative_path == ".":
							module_name = app
						else:
							relative_path = relative_path.replace("/", ".")
							module_name = os.path.splitext(filename)[0]
							module_name = f"{app}.{relative_path}.{module_name}"

						module = nxenv.get_module(module_name)
						candidates.append((module, path, filename))
			compat_preload_test_records_upfront(candidates)

	return NxenvTestCasePreparation(cfg)


@deprecated(
	"nxenv.model.trace.traced_field_context",
	"2024-20-08",
	"v17",
	"use `cls.trace_fields`",
)
def model_trace_traced_field_context(*args, **kwargs):
	from nxenv.tests.classes.context_managers import trace_fields

	return trace_fields(*args, **kwargs)


@deprecated(
	"nxenv.tests.utils.get_dependencies",
	"2024-20-09",
	"v17",
	"refactor to use nxenv.tests.utils.get_missing_records_doctypes",
)
def tests_utils_get_dependencies(doctype):
	"""Get the dependencies for the specified doctype"""
	import nxenv
	from nxenv.tests.utils.generators import get_modules

	module, test_module = get_modules(doctype)
	meta = nxenv.get_meta(doctype)
	link_fields = meta.get_link_fields()

	for df in meta.get_table_fields():
		link_fields.extend(nxenv.get_meta(df.options).get_link_fields())

	options_list = [df.options for df in link_fields]

	if hasattr(test_module, "test_dependencies"):
		options_list += test_module.test_dependencies

	options_list = list(set(options_list))

	if hasattr(test_module, "test_ignore"):
		for doctype_name in test_module.test_ignore:
			if doctype_name in options_list:
				options_list.remove(doctype_name)

	options_list.sort()

	return options_list


@deprecated(
	"nxenv.tests_runner.get_dependencies",
	"2024-20-08",
	"v17",
	"refactor to use nxenv.tests.utils.get_missing_record_doctypes",
)
def test_runner_get_dependencies(doctype):
	return tests_utils_get_dependencies(doctype)


@deprecated(
	"nxenv.get_test_records",
	"2024-20-09",
	"v17",
	"""Please access the global test records pool via cls.globalTestRecords['Some Doc'] -> list.
If not an IntegrationTestCase, use nxenv.tests.utils.load_test_records_for (check return type).
""",
)
def nxenv_get_test_records(doctype):
	import nxenv
	from nxenv.tests.utils.generators import load_test_records_for

	records = load_test_records_for(doctype)
	if isinstance(records, dict):
		_records = []
		for doctype, docs in records.items():
			for doc in docs:
				_doc = doc.copy()
				_doc["doctype"] = doctype
				_records.append(_doc)
		return _records
	return records


def compat_preload_test_records_upfront(candidates: list):
	import json
	import re

	from nxenv.tests.utils import make_test_records

	for module, path, filename in candidates:
		if hasattr(module, "test_dependencies"):
			for doctype in module.test_dependencies:
				make_test_records(doctype, commit=True)
		if hasattr(module, "EXTRA_TEST_RECORD_DEPENDENCIES"):
			for doctype in module.EXTRA_TEST_RECORD_DEPENDENCIES:
				make_test_records(doctype, commit=True)

		if os.path.basename(os.path.dirname(path)) == "doctype":
			# test_data_migration_connector.py > data_migration_connector.json
			test_record_filename = re.sub("^test_", "", filename).replace(".py", ".json")
			test_record_file_path = os.path.join(path, test_record_filename)
			if os.path.exists(test_record_file_path):
				with open(test_record_file_path) as f:
					doc = json.loads(f.read())
					doctype = doc["name"]
					make_test_records(doctype, commit=True)


@deprecated(
	"nxenv.utils.data.get_number_format_info",
	"unknown",
	"v16",
	"Use `NumberFormat.from_string()` from `nxenv.utils.number_format` instead",
)
def get_number_format_info(format: str) -> tuple[str, str, int]:
	"""DEPRECATED: use `NumberFormat.from_string()` from `nxenv.utils.number_format` instead.

	Return the decimal separator, thousands separator and precision for the given number `format` string.

	e.g. get_number_format_info('#,##,###.##') -> ('.', ',', 2)

	Will return ('.', ',', 2) for format strings which can't be guessed.
	"""
	from nxenv.utils.number_format import NUMBER_FORMAT_MAP

	return NUMBER_FORMAT_MAP.get(format) or (".", ",", 2)


@deprecated(
	"modules.txt",
	"2024-11-12",
	"yet unknown",
	"""It has been added for compatibility in addition to the new .nxenv sentinel file inside the module. This is for your info: you don't have to do anything.
""",
)
def boilerplate_modules_txt(dest, app_name, app_title):
	import nxenv

	with open(os.path.join(dest, app_name, app_name, "modules.txt"), "w") as f:
		f.write(nxenv.as_unicode(app_title))
