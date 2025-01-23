# imports - standard imports
import getpass
import os
import subprocess

# imports - module imports
from nxcli.cli import change_uid_msg
from nxcli.config.production_setup import get_supervisor_confdir, is_centos7, service
from nxcli.config.common_site_config import get_config
from nxcli.utils import exec_cmd, get_nxcli_name, get_cmd_output


def is_sudoers_set():
	"""Check if nxcli sudoers is set"""
	cmd = ["sudo", "-n", "nxcli"]
	nxcli_warn = False

	with open(os.devnull, "wb") as f:
		return_code_check = not subprocess.call(cmd, stdout=f)

	if return_code_check:
		try:
			nxcli_warn = change_uid_msg in get_cmd_output(cmd, _raise=False)
		except subprocess.CalledProcessError:
			nxcli_warn = False
		finally:
			return_code_check = return_code_check and nxcli_warn

	return return_code_check


def is_production_set(nxcli_path):
	"""Check if production is set for current nxcli"""
	production_setup = False
	nxcli_name = get_nxcli_name(nxcli_path)

	supervisor_conf_extn = "ini" if is_centos7() else "conf"
	supervisor_conf_file_name = f"{nxcli_name}.{supervisor_conf_extn}"
	supervisor_conf = os.path.join(get_supervisor_confdir(), supervisor_conf_file_name)

	if os.path.exists(supervisor_conf):
		production_setup = production_setup or True

	nginx_conf = f"/etc/nginx/conf.d/{nxcli_name}.conf"

	if os.path.exists(nginx_conf):
		production_setup = production_setup or True

	return production_setup


def execute(nxcli_path):
	"""This patch checks if nxcli sudoers is set and regenerate supervisor and sudoers files"""
	user = get_config(".").get("nxenv_user") or getpass.getuser()

	if is_sudoers_set():
		if is_production_set(nxcli_path):
			exec_cmd(f"sudo nxcli setup supervisor --yes --user {user}")
			service("supervisord", "restart")

		exec_cmd(f"sudo nxcli setup sudoers {user}")
