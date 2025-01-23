"""Module for setting up system and respective nxcli configurations"""


def env():
	from jinja2 import Environment, PackageLoader

	return Environment(loader=PackageLoader("nxcli.config"))
