#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import getpass
import logging
import math
import os
import tarfile
import time

import click
import requests

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class CONFIG:
    base_url = "http://127.0.0.1:8081"


@click.group()
@click.option("--config", default="", help="Configuration file to use.")
def cli(config: str):
    click.echo(f"Config: {config}")


@cli.command()
@click.option("--path", default=".", help="Path to the project.")
def deploy(path: str):
    """Deploy a model to WeCloud"""
    click.echo("Packaging project...")
    tmp_file_name = "/tmp/wecloud-{}-{}.tar.gz".format(getpass.getuser(), math.floor(time.time()))
    with tarfile.open(tmp_file_name, "w:gz") as tar:
        log.debug("path: {}".format(path))
        tar.add(os.path.join(os.getcwd(), path), arcname="")
    click.echo("Packaging project successfully")

    click.echo("Deploying model to WeCloud...")
    resp = requests.post(CONFIG.base_url + "/cli/deploy",
                         files={"file": open(tmp_file_name, "rb")},
                         stream=True)
    log.debug(resp.text)
    if resp.status_code == 200:
        os.remove(tmp_file_name)
        click.echo("Deploying model to WeCloud successfully")


if __name__ == "__main__":
    cli()
