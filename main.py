#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import getpass
import logging
import math
import os
import tarfile
import time
import webbrowser

import click
import requests

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class CONFIG:
    # base_url = "http://127.0.0.1:8081"
    base_url = "https://hz-4.matpool.com:26263"
    deploy_url = "http://101.42.238.229/#/create-deployment"


@click.group()
@click.option("--config", default="", help="Configuration file to use.")
def cli(config: str):
    click.echo(f"Config: {config}")


@cli.command()
@click.option("--path", default=".", help="Path to the project.")
@click.option("--job", default="", help="Name of the job.")
def deploy(path: str, job: str):
    """Deploy a model to WeCloud"""
    if not job:
        job = click.prompt("Please enter a name of the job")
    click.echo("Packaging project...")
    tmp_file_name = "/tmp/wecloud-{}-{}.tar.gz".format(getpass.getuser(), math.floor(time.time()))
    with tarfile.open(tmp_file_name, "w:gz") as tar:
        log.debug("path: {}".format(path))
        tar.add(os.path.join(os.getcwd(), path), arcname="")
    click.echo("Packaging project successfully")

    click.echo("Deploying model to WeCloud...")
    resp = requests.post(CONFIG.base_url + "/cli/deploy",
                         data={'job_name': job},
                         files={"file": open(tmp_file_name, "rb")},
                         stream=True)
    log.debug(resp.text)
    if resp.status_code == 200:
        os.remove(tmp_file_name)
        resp_json = resp.json()
        if resp_json["status"]:
            click.echo("Deploying model to WeCloud successfully")
            click.echo("----------------------------------------")
            click.echo(
                f"""Please visit the following address: "{CONFIG.deploy_url}". Once there, 
select the task "{resp_json['data']['orch_id']}" labeled as "profiling".""")
            webbrowser.open(f"{CONFIG.deploy_url}?orch_id={resp_json['data']['orch_id']}")
        else:
            click.echo(f"Deploying model to WeCloud failed, {resp_json['message']}")
    else:
        click.echo(f"Deploying model to WeCloud failed,{resp.status_code}, {resp.text}")


if __name__ == "__main__":
    cli()
