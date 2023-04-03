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
import yaml
from yaml.parser import ParserError

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class CONFIG:
    base_url = "http://127.0.0.1:8081"
    # base_url = "https://hz-4.matpool.com:26263"
    deploy_url = "http://101.42.238.229/create-deployment"
    config_dir = os.path.join(os.path.expanduser("~"), ".spilot")


def _get_token():
    token = ""
    try:
        with open(os.path.join(CONFIG.config_dir, 'token'), "r") as f:
            token = f.read()
    except FileNotFoundError:
        pass
    return token


@click.group()
@click.option("--config", default="", help="Configuration file to use.")
def cli(config: str):
    click.echo(f"Config: {config}")
    os.makedirs(CONFIG.config_dir, exist_ok=True)


@cli.command()
def login():
    """Login to Serverless Pilot"""
    click.echo("Login to Serverless Pilot")
    click.echo("Please enter your username and password")
    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True)
    click.echo("Login...")
    resp = requests.post(CONFIG.base_url + "/account/login",
                         data={'username': username, 'password': password})
    log.debug(resp.text)
    if resp.status_code == 200:
        resp_json = resp.json()
        token = resp_json["access_token"]
        # save token to ~/.spilot/token
        with open(os.path.join(CONFIG.config_dir, 'token'), "w") as f:
            f.write(token)
        click.echo("Login successfully")
    elif resp.status_code == 401:
        click.echo("Username or password is incorrect")
    else:
        click.echo("Login failed")


@cli.command()
@click.option("--path", default=".", help="Path to the project.")
@click.option("--job", default="", help="Name of the job.")
def deploy(path: str, job: str):
    """Deploy a model to Serverless Pilot"""
    if not job:
        with open(os.path.join(os.getcwd(), path, ".spilot.yaml"), "r") as f:
            try:
                meta_data_dict = yaml.safe_load(f)
            except ParserError as e:
                log.debug("ParserError: {}".format(e))
                pass
            job = meta_data_dict["job_name"]
    if not job:
        job = click.prompt("Please enter a name of the job")
    log.debug("job: {}".format(job))

    click.echo("Packaging project...")
    tmp_file_name = "/tmp/wecloud-{}-{}.tar.gz".format(getpass.getuser(), math.floor(time.time()))
    with tarfile.open(tmp_file_name, "w:gz") as tar:
        log.debug("path: {}".format(path))
        tar.add(os.path.join(os.getcwd(), path), arcname="")
    click.echo("Packaging project successfully")

    click.echo("----------------------------------------")
    click.echo("Deploying model to Serverless Pilot...")
    resp = requests.post(CONFIG.base_url + "/cli/deploy",
                         headers={
                             'Authorization': 'Bearer ' + _get_token(),
                         },
                         data={'job_name': job},
                         files={"file": open(tmp_file_name, "rb")},
                         stream=True)
    log.debug(resp.text)
    if resp.status_code == 200:
        os.remove(tmp_file_name)
        resp_json = resp.json()
        cli_id = resp_json["data"]["cli_id"]
        log.debug("cli_id: {}".format(cli_id))
        status = ""
        while True:
            status_resp = requests.get(f"{CONFIG.base_url}/cli/status/{cli_id}",
                                       headers={
                                           'Authorization': 'Bearer ' + _get_token(),
                                       })
            new_status = status_resp.json()["data"]["status"]
            if status != new_status:
                status = new_status
                click.echo("Deploying model status: {}".format(status))
            time.sleep(2)
            if status == 'stopped':
                break
        click.echo("Deploying model to Serverless Pilot successfully")
        click.echo("----------------------------------------")
        orch_id_resp = requests.get(f"{CONFIG.base_url}/cli/{cli_id}/orch_id",
                                    headers={
                                        'Authorization': 'Bearer ' + _get_token(),
                                    })
        log.debug(orch_id_resp.json())
        orch_id = orch_id_resp.json()["data"]["orch_id"]
        click.echo(
            f"""Please visit the following address: "{CONFIG.deploy_url}". Once there, 
select the task "{orch_id}" labeled as "profiling".""")
        webbrowser.open(f"{CONFIG.deploy_url}?orch_id={orch_id}")


if __name__ == "__main__":
    cli()
