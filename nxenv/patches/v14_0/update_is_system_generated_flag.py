import nxenv


def execute():
	# assuming all customization generated by Admin is system generated customization
	custom_field = nxenv.qb.DocType("Custom Field")
	(
		nxenv.qb.update(custom_field)
		.set(custom_field.is_system_generated, True)
		.where(custom_field.owner == "Administrator")
		.run()
	)

	property_setter = nxenv.qb.DocType("Property Setter")
	(
		nxenv.qb.update(property_setter)
		.set(property_setter.is_system_generated, True)
		.where(property_setter.owner == "Administrator")
		.run()
	)
