import nxenv


# no context object is accepted
def get_context():
	context = nxenv._dict()
	context.body = "Custom Content"
	return context
