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
    # base_url = "http://127.0.0.1:8081"
    # matpool
    # base_url = "https://hz-t2.matpool.com:27075"
    # deploy_url = "http://101.42.238.229/#/create-deployment"
    
    # pkucs
    base_url = "http://115.27.161.208/api/v1"
    deploy_url = "http://115.27.161.208/#/create-deployment"
    
    # xinjin
    # base_url = "http://162.105.175.222:8081"
    # deploy_url = "http://162.105.175.222:8080/#/create-deployment"
    config_dir = os.path.join(os.path.expanduser("~"), ".spilot")


def _get_token():
    token = ""
    try:
        with open(os.path.join(CONFIG.config_dir, 'token'), "r") as f:
            token = f.read()
    except FileNotFoundError:
        token = _login()
    return token


def _login():
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
        return token
    elif resp.status_code == 401:
        click.echo("Username or password is incorrect")
    else:
        click.echo("Login failed")
    return ""


@click.group()
@click.option("--config", default="", help="Configuration file to use.")
def cli(config: str):
    click.echo(f"Config: {config}")
    os.makedirs(CONFIG.config_dir, exist_ok=True)


@cli.command()
def login():
    _login()


@cli.command()
@click.option("--path", default=".", help="Path to the project.")
@click.option("--job", default="", help="Name of the job.")
def deploy(path: str, job: str):
    """Deploy a model to Serverless Pilot"""
    spilot_fn = os.path.join(os.getcwd(), path, ".spilot.yaml")
    _deploy_ts = math.floor(time.time())
    if not job:
        try:
            with open(spilot_fn) as f:
                meta_data_dict = yaml.safe_load(f)
            job = meta_data_dict["job_name"]
        except ParserError as e:
            log.debug("ParserError: {}".format(e))
        except FileNotFoundError as e:
            log.debug("FileNotFoundError: {}".format(e))
    if not job:
        job = click.prompt("Please enter a name of the job")
    log.debug("job: {}".format(job))

    # complete the .spilot.yaml
    meta_data_dict = {
        "job": job,
        "image": "wangqipeng/wecloud_train:v0.2.0",
        "setup": ["pip3 install -r requirements.txt"],
    }
    if not os.path.exists(spilot_fn):
        meta_data_dict["run"] = click.prompt("Please enter the run command")
    else:
        try:
            with open(spilot_fn) as f:
                d = yaml.safe_load(f)
            meta_data_dict["run"] = d["run"].strip()
        except ParserError as e:
            click.echo("yaml format is not correct, exit")
            exit()
    meta_data_dict["run"] = meta_data_dict["run"].split()
    meta_data_dict["profile"] = meta_data_dict["run"].copy()
    print("meta_data_dict", meta_data_dict)
    saved_spilot_fn = "/tmp/.spilot-{}.yaml".format(_deploy_ts)
    with open(saved_spilot_fn, "w") as f:
        yaml.dump(meta_data_dict, f)
    click.echo("save to {}".format(saved_spilot_fn))

    click.echo("Packaging project...")
    tmp_file_name = "/tmp/wecloud-{}-{}.tar.gz".format(getpass.getuser(), _deploy_ts)
    with tarfile.open(tmp_file_name, "w:gz") as tar:
        log.debug("path: {}".format(path))
        tar.add(saved_spilot_fn, arcname=".spilot.yaml")
        tar.add(os.path.join(os.getcwd(), path), arcname="")
    click.echo("Packaging project successfully")
    print(tmp_file_name)

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
            _token = _get_token()
            if _token is None:
                click.echo("Login failed, exit. Please re-login and retry.")
                exit()
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
            f'Please visit the following address: "{CONFIG.deploy_url}". Once there, select the task "{orch_id}" labeled as "profiling".')
        webbrowser.open(f"{CONFIG.deploy_url}?orch_id={orch_id}")
    else:
        click.echo("upload orch faild.")


if __name__ == "__main__":
    cli()
