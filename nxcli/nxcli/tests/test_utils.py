import os
import shutil
import subprocess
import unittest

from nxcli.app import App
from nxcli.nxcli import Nxcli
from nxcli.exceptions import InvalidRemoteException
from nxcli.utils import is_valid_nxenv_branch


class TestUtils(unittest.TestCase):
	def test_app_utils(self):
		git_url = "https://github.com/nxenv/nxenv"
		branch = "develop"
		app = App(name=git_url, branch=branch, nxcli=Nxcli("."))
		self.assertTrue(
			all(
				[
					app.name == git_url,
					app.branch == branch,
					app.tag == branch,
					app.is_url is True,
					app.on_disk is False,
					app.org == "nxenv",
					app.url == git_url,
				]
			)
		)

	def test_is_valid_nxenv_branch(self):
		with self.assertRaises(InvalidRemoteException):
			is_valid_nxenv_branch(
				"https://github.com/nxenv/nxenv.git", nxenv_branch="random-branch"
			)
			is_valid_nxenv_branch(
				"https://github.com/random/random.git", nxenv_branch="random-branch"
			)

		is_valid_nxenv_branch(
			"https://github.com/nxenv/nxenv.git", nxenv_branch="develop"
		)
		is_valid_nxenv_branch(
			"https://github.com/nxenv/nxenv.git", nxenv_branch="v13.29.0"
		)

	def test_app_states(self):
		nxcli_dir = "./sandbox"
		sites_dir = os.path.join(nxcli_dir, "sites")

		if not os.path.exists(sites_dir):
			os.makedirs(sites_dir)

		fake_nxcli = Nxcli(nxcli_dir)

		self.assertTrue(hasattr(fake_nxcli.apps, "states"))

		fake_nxcli.apps.states = {
			"nxenv": {
				"resolution": {"branch": "develop", "commit_hash": "234rwefd"},
				"version": "14.0.0-dev",
			}
		}
		fake_nxcli.apps.update_apps_states()

		self.assertEqual(fake_nxcli.apps.states, {})

		nxenv_path = os.path.join(nxcli_dir, "apps", "nxenv")

		os.makedirs(os.path.join(nxenv_path, "nxenv"))

		subprocess.run(["git", "init"], cwd=nxenv_path, capture_output=True, check=True)

		with open(os.path.join(nxenv_path, "nxenv", "__init__.py"), "w+") as f:
			f.write("__version__ = '11.0'")

		subprocess.run(["git", "add", "."], cwd=nxenv_path, capture_output=True, check=True)
		subprocess.run(
			["git", "config", "user.email", "nxcli-test_app_states@gha.com"],
			cwd=nxenv_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "config", "user.name", "App States Test"],
			cwd=nxenv_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "commit", "-m", "temp"], cwd=nxenv_path, capture_output=True, check=True
		)

		fake_nxcli.apps.update_apps_states(app_name="nxenv")

		self.assertIn("nxenv", fake_nxcli.apps.states)
		self.assertIn("version", fake_nxcli.apps.states["nxenv"])
		self.assertEqual("11.0", fake_nxcli.apps.states["nxenv"]["version"])

		shutil.rmtree(nxcli_dir)

	def test_ssh_ports(self):
		app = App("git@github.com:22:nxenv/nxenv")
		self.assertEqual(
			(app.use_ssh, app.org, app.repo, app.app_name), (True, "nxenv", "nxenv", "nxenv")
		)
