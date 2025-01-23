# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE
"""
nxenv.coverage
~~~~~~~~~~~~~~~~

Coverage settings for nxenv
"""

STANDARD_INCLUSIONS = ["*.py"]

STANDARD_EXCLUSIONS = [
	"*.js",
	"*.xml",
	"*.pyc",
	"*.css",
	"*.less",
	"*.scss",
	"*.vue",
	"*.html",
	"*/test_*",
	"*/node_modules/*",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
]

# tested via commands' test suite
TESTED_VIA_CLI = [
	"*/nxenv/installer.py",
	"*/nxenv/utils/install.py",
	"*/nxenv/utils/scheduler.py",
	"*/nxenv/utils/doctor.py",
	"*/nxenv/build.py",
	"*/nxenv/database/__init__.py",
	"*/nxenv/database/db_manager.py",
	"*/nxenv/database/**/setup_db.py",
]

NXENV_EXCLUSIONS = [
	"*/tests/*",
	"*/commands/*",
	"*/nxenv/change_log/*",
	"*/nxenv/exceptions*",
	"*/nxenv/desk/page/setup_wizard/setup_wizard.py",
	"*/nxenv/coverage.py",
	"*nxenv/setup.py",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
	*TESTED_VIA_CLI,
]


class CodeCoverage:
	"""
	Context manager for handling code coverage.

	This class sets up code coverage measurement for a specific app,
	applying the appropriate inclusion and exclusion patterns.
	"""

	def __init__(self, with_coverage, app, outfile="coverage.xml"):
		self.with_coverage = with_coverage
		self.app = app or "nxenv"
		self.outfile = outfile

	def __enter__(self):
		if self.with_coverage:
			import os

			from coverage import Coverage

			from nxenv.utils import get_nxcli_path

			# Generate coverage report only for app that is being tested
			source_path = os.path.join(get_nxcli_path(), "apps", self.app)
			omit = STANDARD_EXCLUSIONS[:]

			if self.app == "nxenv":
				omit.extend(NXENV_EXCLUSIONS)

			self.coverage = Coverage(source=[source_path], omit=omit, include=STANDARD_INCLUSIONS)
			self.coverage.start()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if self.with_coverage:
			self.coverage.stop()
			self.coverage.save()
			self.coverage.xml_report(outfile=self.outfile)
			print("Saved Coverage")
