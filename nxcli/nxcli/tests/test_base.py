# imports - standard imports
import getpass
import json
import os
import shutil
import subprocess
import sys
import traceback
import unittest

# imports - module imports
from nxcli.utils import paths_in_nxcli, exec_cmd
from nxcli.utils.system import init
from nxcli.nxcli import Nxcli

PYTHON_VER = sys.version_info

NXENV_BRANCH = "version-13-hotfix"
if PYTHON_VER.major == 3:
	if PYTHON_VER.minor >= 10:
		NXENV_BRANCH = "develop"


class TestNxcliBase(unittest.TestCase):
	def setUp(self):
		self.nxclies_path = "."
		self.nxclies = []

	def tearDown(self):
		for nxcli_name in self.nxclies:
			nxcli_path = os.path.join(self.nxclies_path, nxcli_name)
			nxcli = Nxcli(nxcli_path)
			mariadb_password = (
				"travis"
				if os.environ.get("CI")
				else getpass.getpass(prompt="Enter MariaDB root Password: ")
			)

			if nxcli.exists:
				for site in nxcli.sites:
					subprocess.call(
						[
							"nxcli",
							"drop-site",
							site,
							"--force",
							"--no-backup",
							"--root-password",
							mariadb_password,
						],
						cwd=nxcli_path,
					)
				shutil.rmtree(nxcli_path, ignore_errors=True)

	def assert_folders(self, nxcli_name):
		for folder in paths_in_nxcli:
			self.assert_exists(nxcli_name, folder)
		self.assert_exists(nxcli_name, "apps", "nxenv")

	def assert_virtual_env(self, nxcli_name):
		nxcli_path = os.path.abspath(nxcli_name)
		python_path = os.path.abspath(os.path.join(nxcli_path, "env", "bin", "python"))
		self.assertTrue(python_path.startswith(nxcli_path))
		for subdir in ("bin", "lib", "share"):
			self.assert_exists(nxcli_name, "env", subdir)

	def assert_config(self, nxcli_name):
		for config, search_key in (
			("redis_queue.conf", "redis_queue.rdb"),
			("redis_cache.conf", "redis_cache.rdb"),
		):

			self.assert_exists(nxcli_name, "config", config)

			with open(os.path.join(nxcli_name, "config", config)) as f:
				self.assertTrue(search_key in f.read())

	def assert_common_site_config(self, nxcli_name, expected_config):
		common_site_config_path = os.path.join(
			self.nxclies_path, nxcli_name, "sites", "common_site_config.json"
		)
		self.assertTrue(os.path.exists(common_site_config_path))

		with open(common_site_config_path) as f:
			config = json.load(f)

		for key, value in list(expected_config.items()):
			self.assertEqual(config.get(key), value)

	def assert_exists(self, *args):
		self.assertTrue(os.path.exists(os.path.join(*args)))

	def new_site(self, site_name, nxcli_name):
		new_site_cmd = ["nxcli", "new-site", site_name, "--admin-password", "admin"]

		if os.environ.get("CI"):
			new_site_cmd.extend(["--mariadb-root-password", "travis"])

		subprocess.call(new_site_cmd, cwd=os.path.join(self.nxclies_path, nxcli_name))

	def init_nxcli(self, nxcli_name, **kwargs):
		self.nxclies.append(nxcli_name)
		nxenv_tmp_path = "/tmp/nxenv"

		if not os.path.exists(nxenv_tmp_path):
			exec_cmd(
				f"git clone https://github.com/nxenv/nxenv -b {NXENV_BRANCH} --depth 1 --origin upstream {nxenv_tmp_path}"
			)

		kwargs.update(
			dict(
				python=sys.executable,
				no_procfile=True,
				no_backups=True,
				nxenv_path=nxenv_tmp_path,
			)
		)

		if not os.path.exists(os.path.join(self.nxclies_path, nxcli_name)):
			init(nxcli_name, **kwargs)
			exec_cmd(
				"git remote set-url upstream https://github.com/nxenv/nxenv",
				cwd=os.path.join(self.nxclies_path, nxcli_name, "apps", "nxenv"),
			)

	def file_exists(self, path):
		if os.environ.get("CI"):
			return not subprocess.call(["sudo", "test", "-f", path])
		return os.path.isfile(path)

	def get_traceback(self):
		exc_type, exc_value, exc_tb = sys.exc_info()
		trace_list = traceback.format_exception(exc_type, exc_value, exc_tb)
		return "".join(str(t) for t in trace_list)
