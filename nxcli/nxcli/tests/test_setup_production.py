# imports - standard imports
import getpass
import os
import pathlib
import re
import subprocess
import time
import unittest

# imports - module imports
from nxcli.utils import exec_cmd, get_cmd_output, which
from nxcli.config.production_setup import get_supervisor_confdir
from nxcli.tests.test_base import TestNxcliBase


class TestSetupProduction(TestNxcliBase):
	def test_setup_production(self):
		user = getpass.getuser()

		for nxcli_name in ("test-nxcli-1", "test-nxcli-2"):
			nxcli_path = os.path.join(os.path.abspath(self.nxclies_path), nxcli_name)
			self.init_nxcli(nxcli_name)
			exec_cmd(f"sudo nxcli setup production {user} --yes", cwd=nxcli_path)
			self.assert_nginx_config(nxcli_name)
			self.assert_supervisor_config(nxcli_name)
			self.assert_supervisor_process(nxcli_name)

		self.assert_nginx_process()
		exec_cmd(f"sudo nxcli setup sudoers {user}")
		self.assert_sudoers(user)

		for nxcli_name in self.nxclies:
			nxcli_path = os.path.join(os.path.abspath(self.nxclies_path), nxcli_name)
			exec_cmd("sudo nxcli disable-production", cwd=nxcli_path)

	def production(self):
		try:
			self.test_setup_production()
		except Exception:
			print(self.get_traceback())

	def assert_nginx_config(self, nxcli_name):
		conf_src = os.path.join(
			os.path.abspath(self.nxclies_path), nxcli_name, "config", "nginx.conf"
		)
		conf_dest = f"/etc/nginx/conf.d/{nxcli_name}.conf"

		self.assertTrue(self.file_exists(conf_src))
		self.assertTrue(self.file_exists(conf_dest))

		# symlink matches
		self.assertEqual(os.path.realpath(conf_dest), conf_src)

		# file content
		with open(conf_src) as f:
			f = f.read()

			for key in (
				f"upstream {nxcli_name}-nxenv",
				f"upstream {nxcli_name}-socketio-server",
			):
				self.assertTrue(key in f)

	def assert_nginx_process(self):
		out = get_cmd_output("sudo nginx -t 2>&1")
		self.assertTrue(
			"nginx: configuration file /etc/nginx/nginx.conf test is successful" in out
		)

	def assert_sudoers(self, user):
		sudoers_file = "/etc/sudoers.d/nxenv"
		service = which("service")
		nginx = which("nginx")

		self.assertTrue(self.file_exists(sudoers_file))

		if os.environ.get("CI"):
			sudoers = subprocess.check_output(["sudo", "cat", sudoers_file]).decode("utf-8")
		else:
			sudoers = pathlib.Path(sudoers_file).read_text()
		self.assertTrue(f"{user} ALL = (root) NOPASSWD: {service} nginx *" in sudoers)
		self.assertTrue(f"{user} ALL = (root) NOPASSWD: {nginx}" in sudoers)

	def assert_supervisor_config(self, nxcli_name, use_rq=True):
		conf_src = os.path.join(
			os.path.abspath(self.nxclies_path), nxcli_name, "config", "supervisor.conf"
		)

		supervisor_conf_dir = get_supervisor_confdir()
		conf_dest = f"{supervisor_conf_dir}/{nxcli_name}.conf"

		self.assertTrue(self.file_exists(conf_src))
		self.assertTrue(self.file_exists(conf_dest))

		# symlink matches
		self.assertEqual(os.path.realpath(conf_dest), conf_src)

		# file content
		with open(conf_src) as f:
			f = f.read()

			tests = [
				f"program:{nxcli_name}-nxenv-web",
				f"program:{nxcli_name}-redis-cache",
				f"program:{nxcli_name}-redis-queue",
				f"group:{nxcli_name}-web",
				f"group:{nxcli_name}-workers",
				f"group:{nxcli_name}-redis",
			]

			if not os.environ.get("CI"):
				tests.append(f"program:{nxcli_name}-node-socketio")

			if use_rq:
				tests.extend(
					[
						f"program:{nxcli_name}-nxenv-schedule",
						f"program:{nxcli_name}-nxenv-default-worker",
						f"program:{nxcli_name}-nxenv-short-worker",
						f"program:{nxcli_name}-nxenv-long-worker",
					]
				)

			else:
				tests.extend(
					[
						f"program:{nxcli_name}-nxenv-workerbeat",
						f"program:{nxcli_name}-nxenv-worker",
						f"program:{nxcli_name}-nxenv-longjob-worker",
						f"program:{nxcli_name}-nxenv-async-worker",
					]
				)

			for key in tests:
				self.assertTrue(key in f)

	def assert_supervisor_process(self, nxcli_name, use_rq=True, disable_production=False):
		out = get_cmd_output("supervisorctl status")

		while "STARTING" in out:
			print("Waiting for all processes to start...")
			time.sleep(10)
			out = get_cmd_output("supervisorctl status")

		tests = [
			r"{nxcli_name}-web:{nxcli_name}-nxenv-web[\s]+RUNNING",
			# Have commented for the time being. Needs to be uncommented later on. Nxcli is failing on travis because of this.
			# It works on one nxcli and fails on another.giving FATAL or BACKOFF (Exited too quickly (process log may have details))
			# "{nxcli_name}-web:{nxcli_name}-node-socketio[\s]+RUNNING",
			r"{nxcli_name}-redis:{nxcli_name}-redis-cache[\s]+RUNNING",
			r"{nxcli_name}-redis:{nxcli_name}-redis-queue[\s]+RUNNING",
		]

		if use_rq:
			tests.extend(
				[
					r"{nxcli_name}-workers:{nxcli_name}-nxenv-schedule[\s]+RUNNING",
					r"{nxcli_name}-workers:{nxcli_name}-nxenv-default-worker-0[\s]+RUNNING",
					r"{nxcli_name}-workers:{nxcli_name}-nxenv-short-worker-0[\s]+RUNNING",
					r"{nxcli_name}-workers:{nxcli_name}-nxenv-long-worker-0[\s]+RUNNING",
				]
			)

		else:
			tests.extend(
				[
					r"{nxcli_name}-workers:{nxcli_name}-nxenv-workerbeat[\s]+RUNNING",
					r"{nxcli_name}-workers:{nxcli_name}-nxenv-worker[\s]+RUNNING",
					r"{nxcli_name}-workers:{nxcli_name}-nxenv-longjob-worker[\s]+RUNNING",
					r"{nxcli_name}-workers:{nxcli_name}-nxenv-async-worker[\s]+RUNNING",
				]
			)

		for key in tests:
			if disable_production:
				self.assertFalse(re.search(key, out))
			else:
				self.assertTrue(re.search(key, out))


if __name__ == "__main__":
	unittest.main()
