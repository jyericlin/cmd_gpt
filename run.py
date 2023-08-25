# Copyright (c) 2023 Jieyu Lin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

import fire
import yaml
from loguru import logger


def setup_logging(logger_level="INFO"):
    logger.remove()
    logger.add(
        sink=os.path.join(os.path.dirname(__file__), "log/run.log"),
        level=logger_level,
        rotation="10 MB",
        compression="zip",
        serialize=True,
    )
    logger.add(
        sys.stderr,
        level=logger_level,
    )

def source_env(path):
    config = yaml.safe_load(open(path, "r"))
    for key, value in config.items():
        os.environ[key] = value
    return config

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config/key.yaml")
    return source_env(config_path)

def run(prompt: str, logger_level:str="INFO"):
    config = load_config()
    setup_logging(logger_level)
    from cmd_gpt.agent.deployment_cmd_agent import DeploymentCmdAgent
    agent = DeploymentCmdAgent(config)
    agent.run(prompt)
    agent.close()


if __name__ == "__main__":
    fire.Fire(run)
