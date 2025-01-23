import nxenv


def execute():
	"""Remove stale docfields from legacy version"""
	nxenv.db.delete("DocField", {"options": "Data Import", "parent": "Data Import Legacy"})
