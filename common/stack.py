"""Functionality for determining the runtime environment"""
import importlib
import logging
import platform
import re
import subprocess
import sys

REQUIRED_PY_DEPENDENCIES = ("enderchest", "gsb", "pygit2")
OPTIONAL_PY_DEPENDENCIES = (
    "paramiko",
    "pytest",
)

LOGGER = logging.getLogger(__name__)


def get_dependency_versions() -> dict[str, str]:
    """Report on a list of installed dependencies

    Returns
    -------
    dict
        A map of Python package names to their installed versions (an empty
        string means that package is not installed)
    """
    report: dict[str, str] = {}
    for component_list in (REQUIRED_PY_DEPENDENCIES, OPTIONAL_PY_DEPENDENCIES):
        for component in component_list:
            try:
                report[component] = importlib.import_module(component).__version__
            except (ModuleNotFoundError, AttributeError):
                report[component] = ""
    return report


def get_stack() -> dict[str, str]:
    """Report the system OS and architecture, the Python version and the versions
    of any non-Python system components

    Returns
    -------
    dict
        A map system descriptors to the version information (and empty string
        means that component is not installed or available)
    """
    uname = platform.uname()

    return {
        "os": f"{uname.system} {uname.release}",
        "architecture": uname.machine,
        "Python": sys.version,
        "Rsync": _get_rsync_version(),
    }


def _get_rsync_version() -> str:
    """Determine the installed version of Rsync

    Notes
    -----
    - If Rsync is not installed or is too old to be used, this will return
      an empty string
    """
    try:
        result = subprocess.run(
            ["rsync", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.stderr:
            LOGGER.error(result.stderr.decode("utf-8"))

        head = result.stdout.decode("utf-8").splitlines()[0]
        if match := re.match(
            r"^rsync[\s]+version ([0-9]+).([0-9]+).([0-9]+)",
            head,
        ):
            major, minor, *_ = match.groups()
            if int(major) < 3 or (int(major) == 3 and int(minor) < 2):
                LOGGER.error("%s is too old", head)
                return ""
            return head[len("rsync") :].strip()
        else:
            LOGGER.error("Could not parse output message:\n%s", head)
            return ""

    except (FileNotFoundError, IndexError):
        return ""
