# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt


import functools

import nxenv


@nxenv.whitelist()
def get_google_fonts():
	return _get_google_fonts()


@functools.lru_cache
def _get_google_fonts():
	file_path = nxenv.get_app_path("nxenv", "data", "google_fonts.json")
	return nxenv.parse_json(nxenv.read_file(file_path))
