# Makefile

# Define variables
VENV_DIR = venv
PYTHON = python3
REQUIREMENTS = docker/requirements-test.txt
SCRIPT = main.py

# Create virtual environment
$(VENV_DIR)/bin/activate:
	$(PYTHON) -m venv $(VENV_DIR)

# Install dependencies
install: $(VENV_DIR)/bin/activate
	$(VENV_DIR)/bin/pip install -r $(REQUIREMENTS)

# Run the Python script
run: install
	$(VENV_DIR)/bin/python $(SCRIPT)
	install-editable: $(VENV_DIR)/bin/activate
	$(VENV_DIR)/bin/pip install -e .

# Clean up the virtual environment
clean:
	rm -rf $(VENV_DIR)
	# Install the current package in editable mode

.PHONY: install run clean
