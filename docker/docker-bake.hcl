# Docker Buildx Bake build definition file
# Reference: https://github.com/docker/buildx/blob/master/docs/reference/buildx_bake.md

variable "REGISTRY_USER" {
    default = "nxenv"
}

variable PYTHON_VERSION {
    default = "3.11.6"
}
variable NODE_VERSION {
    default = "18.18.2"
}

variable "NXENV_VERSION" {
    default = "develop"
}

variable "ERPNEXT_VERSION" {
    default = "develop"
}

variable "NXENV_REPO" {
    default = "https://github.com/nxenv/nxenv"
}

variable "ERPNEXT_REPO" {
    default = "https://github.com/nxenv/erpnext"
}

variable "NXCLI_REPO" {
    default = "https://github.com/nxenv/nxcli"
}

variable "LATEST_NXCLI_RELEASE" {
    default = "latest"
}

# Nxcli image

target "nxcli" {
    args = {
        GIT_REPO = "${NXCLI_REPO}"
    }
    context = "images/nxcli"
    target = "nxcli"
    tags = [
        "nxenv/nxcli:${LATEST_NXCLI_RELEASE}",
        "nxenv/nxcli:latest",
    ]
}

target "nxcli-test" {
    inherits = ["nxcli"]
    target = "nxcli-test"
}

# Main images
# Base for all other targets

group "default" {
    targets = ["erpnext", "base", "build"]
}

function "tag" {
    params = [repo, version]
    result = [
      # Push nxenv or erpnext branch as tag
      "${REGISTRY_USER}/${repo}:${version}",
      # If `version` param is develop (development build) then use tag `latest`
      "${version}" == "develop" ? "${REGISTRY_USER}/${repo}:latest" : "${REGISTRY_USER}/${repo}:${version}",
      # Make short tag for major version if possible. For example, from v13.16.0 make v13.
      can(regex("(v[0-9]+)[.]", "${version}")) ? "${REGISTRY_USER}/${repo}:${regex("(v[0-9]+)[.]", "${version}")[0]}" : "",
      # Make short tag for major version if possible. For example, from v13.16.0 make version-13.
      can(regex("(v[0-9]+)[.]", "${version}")) ? "${REGISTRY_USER}/${repo}:version-${regex("([0-9]+)[.]", "${version}")[0]}" : "",
    ]
}

target "default-args" {
    args = {
        NXENV_PATH = "${NXENV_REPO}"
        ERPNEXT_PATH = "${ERPNEXT_REPO}"
        NXCLI_REPO = "${NXCLI_REPO}"
        NXENV_BRANCH = "${NXENV_VERSION}"
        ERPNEXT_BRANCH = "${ERPNEXT_VERSION}"
        PYTHON_VERSION = "${PYTHON_VERSION}"
        NODE_VERSION = "${NODE_VERSION}"
    }
}

target "erpnext" {
    inherits = ["default-args"]
    context = "."
    dockerfile = "images/production/Containerfile"
    target = "erpnext"
    tags = tag("erpnext", "${ERPNEXT_VERSION}")
}

target "base" {
    inherits = ["default-args"]
    context = "."
    dockerfile = "images/production/Containerfile"
    target = "base"
    tags = tag("base", "${NXENV_VERSION}")
}

target "build" {
    inherits = ["default-args"]
    context = "."
    dockerfile = "images/production/Containerfile"
    target = "build"
    tags = tag("build", "${ERPNEXT_VERSION}")
}
