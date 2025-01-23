# imports - standard imports
import json
import os
import subprocess
import unittest

# imports - third paty imports
import git

# imports - module imports
from nxcli.utils import exec_cmd
from nxcli.app import App
from nxcli.tests.test_base import NXENV_BRANCH, TestNxcliBase
from nxcli.nxcli import Nxcli


# changed from nxenv_theme because it wasn't maintained and incompatible,
# chat app & wiki was breaking too. hopefully nxenv_docs will be maintained
# for longer since docs.erpnext.com is powered by it ;)
TEST_NXENV_APP = "nxenv_docs"


class TestNxcliInit(TestNxcliBase):
	def test_utils(self):
		self.assertEqual(subprocess.call("nxcli"), 0)

	def test_init(self, nxcli_name="test-nxcli", **kwargs):
		self.init_nxcli(nxcli_name, **kwargs)
		app = App("file:///tmp/nxenv")
		self.assertTupleEqual(
			(app.mount_path, app.url, app.repo, app.app_name, app.org),
			("/tmp/nxenv", "file:///tmp/nxenv", "nxenv", "nxenv", "nxenv"),
		)
		self.assert_folders(nxcli_name)
		self.assert_virtual_env(nxcli_name)
		self.assert_config(nxcli_name)
		test_nxcli = Nxcli(nxcli_name)
		app = App("nxenv", nxcli=test_nxcli)
		self.assertEqual(app.from_apps, True)

	def basic(self):
		try:
			self.test_init()
		except Exception:
			print(self.get_traceback())

	def test_multiple_nxclies(self):
		for nxcli_name in ("test-nxcli-1", "test-nxcli-2"):
			self.init_nxcli(nxcli_name, skip_assets=True)

		self.assert_common_site_config(
			"test-nxcli-1",
			{
				"webserver_port": 8000,
				"socketio_port": 9000,
				"file_watcher_port": 6787,
				"redis_queue": "redis://127.0.0.1:11000",
				"redis_socketio": "redis://127.0.0.1:13000",
				"redis_cache": "redis://127.0.0.1:13000",
			},
		)

		self.assert_common_site_config(
			"test-nxcli-2",
			{
				"webserver_port": 8001,
				"socketio_port": 9001,
				"file_watcher_port": 6788,
				"redis_queue": "redis://127.0.0.1:11001",
				"redis_socketio": "redis://127.0.0.1:13001",
				"redis_cache": "redis://127.0.0.1:13001",
			},
		)

	def test_new_site(self):
		nxcli_name = "test-nxcli"
		site_name = "test-site.local"
		nxcli_path = os.path.join(self.nxclies_path, nxcli_name)
		site_path = os.path.join(nxcli_path, "sites", site_name)
		site_config_path = os.path.join(site_path, "site_config.json")

		self.init_nxcli(nxcli_name)
		self.new_site(site_name, nxcli_name)

		self.assertTrue(os.path.exists(site_path))
		self.assertTrue(os.path.exists(os.path.join(site_path, "private", "backups")))
		self.assertTrue(os.path.exists(os.path.join(site_path, "private", "files")))
		self.assertTrue(os.path.exists(os.path.join(site_path, "public", "files")))
		self.assertTrue(os.path.exists(site_config_path))

		with open(site_config_path) as f:
			site_config = json.loads(f.read())

			for key in ("db_name", "db_password"):
				self.assertTrue(key in site_config)
				self.assertTrue(site_config[key])

	def test_get_app(self):
		self.init_nxcli("test-nxcli", skip_assets=True)
		nxcli_path = os.path.join(self.nxclies_path, "test-nxcli")
		exec_cmd(f"nxcli get-app {TEST_NXENV_APP} --skip-assets", cwd=nxcli_path)
		self.assertTrue(os.path.exists(os.path.join(nxcli_path, "apps", TEST_NXENV_APP)))
		app_installed_in_env = TEST_NXENV_APP in subprocess.check_output(
			["nxcli", "pip", "freeze"], cwd=nxcli_path
		).decode("utf8")
		self.assertTrue(app_installed_in_env)

	@unittest.skipIf(NXENV_BRANCH != "develop", "only for develop branch")
	def test_get_app_resolve_deps(self):
		NXENV_APP = "healthcare"
		self.init_nxcli("test-nxcli", skip_assets=True)
		nxcli_path = os.path.join(self.nxclies_path, "test-nxcli")
		exec_cmd(f"nxcli get-app {NXENV_APP} --resolve-deps --skip-assets", cwd=nxcli_path)
		self.assertTrue(os.path.exists(os.path.join(nxcli_path, "apps", NXENV_APP)))

		states_path = os.path.join(nxcli_path, "sites", "apps.json")
		self.assertTrue(os.path.exists(states_path))

		with open(states_path) as f:
			states = json.load(f)

		self.assertTrue(NXENV_APP in states)

	def test_install_app(self):
		nxcli_name = "test-nxcli"
		site_name = "install-app.test"
		nxcli_path = os.path.join(self.nxclies_path, "test-nxcli")

		self.init_nxcli(nxcli_name, skip_assets=True)
		exec_cmd(
			f"nxcli get-app {TEST_NXENV_APP} --branch master --skip-assets", cwd=nxcli_path
		)

		self.assertTrue(os.path.exists(os.path.join(nxcli_path, "apps", TEST_NXENV_APP)))

		# check if app is installed
		app_installed_in_env = TEST_NXENV_APP in subprocess.check_output(
			["nxcli", "pip", "freeze"], cwd=nxcli_path
		).decode("utf8")
		self.assertTrue(app_installed_in_env)

		# create and install app on site
		self.new_site(site_name, nxcli_name)
		installed_app = not exec_cmd(
			f"nxcli --site {site_name} install-app {TEST_NXENV_APP}",
			cwd=nxcli_path,
			_raise=False,
		)

		if installed_app:
			app_installed_on_site = subprocess.check_output(
				["nxcli", "--site", site_name, "list-apps"], cwd=nxcli_path
			).decode("utf8")
			self.assertTrue(TEST_NXENV_APP in app_installed_on_site)

	def test_remove_app(self):
		self.init_nxcli("test-nxcli", skip_assets=True)
		nxcli_path = os.path.join(self.nxclies_path, "test-nxcli")

		exec_cmd(
			f"nxcli get-app {TEST_NXENV_APP} --branch master --overwrite --skip-assets",
			cwd=nxcli_path,
		)
		exec_cmd(f"nxcli remove-app {TEST_NXENV_APP}", cwd=nxcli_path)

		with open(os.path.join(nxcli_path, "sites", "apps.txt")) as f:
			self.assertFalse(TEST_NXENV_APP in f.read())
		self.assertFalse(
			TEST_NXENV_APP
			in subprocess.check_output(["nxcli", "pip", "freeze"], cwd=nxcli_path).decode("utf8")
		)
		self.assertFalse(os.path.exists(os.path.join(nxcli_path, "apps", TEST_NXENV_APP)))

	def test_switch_to_branch(self):
		self.init_nxcli("test-nxcli", skip_assets=True)
		nxcli_path = os.path.join(self.nxclies_path, "test-nxcli")
		app_path = os.path.join(nxcli_path, "apps", "nxenv")

		# * chore: change to 14 when avalible
		prevoius_branch = "version-13"
		if NXENV_BRANCH != "develop":
			# assuming we follow `version-#`
			prevoius_branch = f"version-{int(NXENV_BRANCH.split('-')[1]) - 1}"

		successful_switch = not exec_cmd(
			f"nxcli switch-to-branch {prevoius_branch} nxenv --upgrade",
			cwd=nxcli_path,
			_raise=False,
		)
		if successful_switch:
			app_branch_after_switch = str(git.Repo(path=app_path).active_branch)
			self.assertEqual(prevoius_branch, app_branch_after_switch)

		successful_switch = not exec_cmd(
			f"nxcli switch-to-branch {NXENV_BRANCH} nxenv --upgrade",
			cwd=nxcli_path,
			_raise=False,
		)
		if successful_switch:
			app_branch_after_second_switch = str(git.Repo(path=app_path).active_branch)
			self.assertEqual(NXENV_BRANCH, app_branch_after_second_switch)


if __name__ == "__main__":
	unittest.main()
