VERSION = "5.0.0-dev"
PROJECT_NAME = "nxenv-nxcli"
NXENV_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_nxenv_version(nxcli_path="."):
	from .utils.app import get_current_nxenv_version

	global NXENV_VERSION
	if not NXENV_VERSION:
		NXENV_VERSION = get_current_nxenv_version(nxcli_path=nxcli_path)
