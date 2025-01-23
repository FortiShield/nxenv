import os

import nxenv


def execute():
	site = nxenv.local.site

	log_folder = os.path.join(site, "logs")
	if not os.path.exists(log_folder):
		os.mkdir(log_folder)
