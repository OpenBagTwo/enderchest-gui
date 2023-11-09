"""Functionality for parsing and storing settings"""
import datetime as dt
import json
import logging
import os
import tomllib
from pathlib import Path
from typing import Self, TypeAlias

from enderchest import EnderChest
from enderchest.filesystem import ender_chest_config
from gsb.manifest import Manifest as GSB_Manifest

from ._version import get_versions

LOGGER = logging.getLogger(__name__)

_ConfigDict: TypeAlias = dict[str, str | tuple[str, ...]]


class Config:
    """Application settings

    Attributes
    ----------
    ender_chests : list of EnderChests
        The EnderChests to be managed by this application
    saves : list of GSB Manifests
        The GSB save repos to be managed by this application
    """

    def __init__(self) -> None:
        self._ender_chests: dict[Path, EnderChest] = {}
        self._saves: dict[Path, GSB_Manifest] = {}
        try:
            if minecraft_root := os.getenv("MINECRAFT_ROOT"):
                self.register_enderchest(Path(minecraft_root))
        except (ValueError, OSError) as env_chest_load_fail:
            LOGGER.error(
                "Failed to load chest from $MINECRAFT_ROOT: %s\n%s",
                minecraft_root,
                env_chest_load_fail,
            )

    @property
    def ender_chests(self) -> list[EnderChest]:
        return list(self._ender_chests.values())

    @property
    def saves(self) -> list[GSB_Manifest]:
        return list(self._saves.values())

    def register_enderchest(self, minecraft_root: Path) -> Self:
        """Register (or re-register) an EnderChest to manage

        Parameters
        ----------
        minecraft_root : Path
            The path to the "minecraft root" (the parent directory of the
            EnderChest folder)

        Returns
        -------
        self

        Raises
        ------
        OSError
            If the specified file cannot be found or cannot be read
        ValueError
            If the config file at that location cannot be parsed
        """
        chest = EnderChest.from_cfg(ender_chest_config(minecraft_root.expanduser()))
        self._ender_chests[minecraft_root] = chest
        return self

    def register_save(self, manifest_path: Path) -> Self:
        """Register (or re-register) a GSB save repo to manage

        Parameters
        ----------
        manifest_path: Path
            The path to the .gsb_manifest file

        Returns
        -------
        self

        Raises
        ------
        OSError
            If the specified file cannot be found or cannot be read
        ValueError
            If the config file at that location cannot be parsed
        """
        # TODO: rework will be required when
        #       https://github.com/OpenBagTwo/gsb/issues/29 is implemented
        save = GSB_Manifest.of(manifest_path.expanduser().parent)
        self._saves[save.root] = save
        return self

    def write(self, config_file: Path | None = None) -> str:
        """Write the application configuration to TOML

        Parameters
        ----------
        config_file : Path, optional
            The path to the config file, assuming you'd like to write the
            contents to file

        Returns
        -------
        str
            A TOML-syntax rendering of the application's config

        Raises
        ------
        OSError
            If the specified config file cannot be written to
        """
        as_dict = {
            "generated_by_enderchest_gui": get_versions()["version"],
            "last_modified": dt.datetime.now().isoformat(sep=" "),
            "ender_chests": [
                str(minecraft_root) for minecraft_root in self._ender_chests
            ],
            "saves": [str(manifest_path) for manifest_path in self._saves],
        }
        dumped = _to_toml(as_dict)
        if config_file:
            config_file.write_text(dumped)
        return dumped

    @classmethod
    def from_config(cls, config_file: Path) -> Self:
        """Load an application configuration from file

        Parameters
        ----------
        config_file : Path
            The path of the configuration file

        Returns
        -------
        Config
            The parsed and loaded configuration file
        """
        as_dict: _ConfigDict = tomllib.loads(config_file.read_text())
        config = cls()
        for minecraft_root in as_dict["ender_chests"]:
            try:
                config.register_enderchest(Path(minecraft_root))
            except (ValueError, OSError) as load_error:
                LOGGER.error(
                    "Failed to load chest from %s\n%s",
                    minecraft_root,
                    load_error,
                )
        for manifest_path in as_dict["saves"]:
            try:
                config.register_save(Path(manifest_path))
            except (ValueError, OSError) as load_error:
                LOGGER.error(
                    "Failed to load GSB manifest from %s\n%s",
                    manifest_path,
                    load_error,
                )
        return config


def _to_toml(config_dict: _ConfigDict) -> str:
    """While Python 3.11 added native support for *parsing* TOML configurations,
    it didn't include an API for *writing* them (this was an intentional part
    of the PEP:
    https://peps.python.org/pep-0680/#including-an-api-for-writing-toml).

    Because the Config class is so simple, I'm rolling my own writer rather
    than adding a dependency on a third-party library. That being said, I'm
    abstracting that writer out in case I change my mind later. :D

    Parameters
    ----------
    config_dict : dict
        A dict version of the config containing the entries that should be
        written to file

    Returns
    -------
    str
        The manifest serialized as a TOML-compatible str

    Notes
    -----
    This doesn't take an actual config as a parameter to give better control
    over what information is written
    """
    dumped = ""
    for key, value in config_dict.items():
        dumped += f"{key} = "
        if isinstance(value, str):
            # it's honestly shocking how often I rely on json.dump for str escaping
            dumped += f"{json.dumps(value)}\n"
        else:
            dumped += "["
            for entry in sorted(set(value)):
                dumped += f"\n    {json.dumps(entry)},"
            dumped += "\n]\n"
    return dumped
