# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Elon Gasper, Richard Leeds, Kirill Hrymailo
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import os
import json
from typing import Optional


def load_neon_mq_config():
    """
    Locates and loads global MQ configuration
    """
    valid_config_paths = (
        os.path.expanduser("~/.config/neon/mq_config.json"),
        os.path.expanduser("~/.local/share/neon/credentials.json"),
    )
    config = None
    for conf in valid_config_paths:
        if os.path.isfile(conf):
            config = Configuration().from_file(conf).config_data
            break
    if not config:
        return
    if "MQ" in config.keys():
        return config["MQ"]
    else:
        return config


class Configuration:
    def __init__(self, file_path: Optional[str] = None):
        self._config_data = dict()
        if file_path:
            self.from_file(file_path)

    def from_file(self, file_path: str):
        with open(os.path.expanduser(file_path)) as input_file:
            self._config_data = json.load(input_file)
        return self

    def from_dict(self, config_data: dict):
        self._config_data = config_data
        return self

    @property
    def config_data(self) -> dict:
        return self._config_data

    @config_data.setter
    def config_data(self, value):
        if not isinstance(value, dict):
            raise TypeError(f'Type: {type(value)} not supported')
        self._config_data = value
