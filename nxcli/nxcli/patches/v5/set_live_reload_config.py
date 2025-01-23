from nxcli.config.common_site_config import update_config


def execute(nxcli_path):
	update_config({"live_reload": True}, nxcli_path)
