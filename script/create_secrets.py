#!/usr/bin/python
"""A script to create the required secrets in one namespace by copying them
from another namespace
"""

import base64
import fire
from google.cloud import storage
from kubernetes import client as k8s_client
from kubernetes import config as k8s_config
from kubernetes.client import rest
import logging
import yaml
import os
import re
import subprocess

DEV_ENVIRONMENT = "dev"
PROD_ENVIRONMENT = "prod"

# The namespace for the dev environment.
DEV_NAMESPACE = "label-bot-dev"
PROD_NAMESPACE = "label-bot-prod"

GCS_REGEX = re.compile("gs://([^/]*)(/.*)?")

def split_gcs_uri(gcs_uri):
  """Split a GCS URI into bucket and path."""
  m = GCS_REGEX.match(gcs_uri)
  bucket = m.group(1)
  path = ""
  if m.group(2):
    path = m.group(2).lstrip("/")
  return bucket, path

def secret_exists(namespace, name, client):
  api = k8s_client.CoreV1Api(client)

  try:
    api.read_namespaced_secret(name, namespace)
    return True
  except rest.ApiException as e:
    if e.status != 404:
      raise

  return False

def _read_gcs_path(gcs_path):
  bucket_name, blob_name = split_gcs_uri(gcs_path)

  storage_client = storage.Client()

  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(blob_name)
  contents = blob.download_as_string().decode()

  return contents

class SecretCreator:

  @staticmethod
  def _secret_from_gcs(secret_name, gcs_path):
    bucket_name, blob_name = split_gcs_uri(gcs_path)

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    contents = blob.download_as_string().decode()

    file_name = os.path.basename(blob_name)
    namespace, name = secret_name.split("/", 1)
    subprocess.check_call(["kubectl", "-n", namespace, "create",
                           "secret", "generic",
                           name,
                           f"--from-literal=f{file_name}={contents}"])
  @staticmethod
  def copy_secret(source, dest):
    """Create the dev version of the secrets.

    Args:
      source: {namespace}/{secret name}
      dest: {namespace}/{secret name}
    """
    src_namespace, src_name = source.split("/", 1)
    dest_namespace, dest_name = dest.split("/", 1)

    data = subprocess.check_output(["kubectl", "-n", src_namespace, "get",
                                    "secrets", src_name, "-o",
                                    "yaml"])

    encoded = yaml.load(data)
    decoded = {}

    for k, v in encoded["data"].items():
      decoded[k] = base64.b64decode(v).decode()

    command = ["kubectl", "create", "-n", dest_namespace, "secret",
               "generic", dest_name]

    for k, v in decoded.items():
      command.append(f"--from-literal={k}={v}")

    subprocess.check_call(command)

  @staticmethod
  def create(env):
    """Create the secrets for the dev environment.

    Args:
      env: The environment to create the secrets in.
    """

    if env == DEV_ENVIRONMENT:
      namespace = DEV_NAMESPACE
      github_app_pem_key = ("gs://issue-label-bot-dev_secrets/"
                           "kf-label-bot-dev.2019-12-30.private-key.pem")
      webhook_gcs = ("gs://issue-label-bot-dev_secrets/"
                     "kf-label-bot-dev.webhook.secret")
    elif env == PROD_ENVIRONMENT:
      namespace = PROD_NAMESPACE
      github_app_pem_key = ("gs://github-probots_secrets/"
                            "issue-label-bot-github-app.private-key.pem")
      webhook_gcs = ("gs://github-probots_secrets/"
                     "issue-label-bot-prod.webhook.secret")
    else:
      raise ValueError(f"env={env} is not an allowed value; must be "
                       f"{DEV_ENVIRONMENT} or {PROD_ENVIRONMENT}")

    k8s_config.load_kube_config(persist_config=False)

    client = k8s_client.ApiClient()

    if secret_exists(namespace, "user-gcp-sa", client):
      logging.warning(f"Secret {namespace}/user-gcp-sa already exists; "
                      f"Not recreating it.")
    else:
      # We get a GCP secret by copying it from the kubeflow namespace.
      SecretCreator.copy_secret("kubeflow/user-gcp-sa",
                                f"{namespace}/user-gcp-sa")

    if secret_exists(namespace, "github-app", client):
      logging.warning(f"Secret {namespace}/github-app already exists; "
                      f"Not recreating it.")
    else:
      # Create the secret containing the PEM key for the github app
      SecretCreator._secret_from_gcs(f"{namespace}/github-app", github_app_pem_key)

    # Create the inference secret containing the postgres database with
    # postgres secret and the webhook secret
    inference_secret = "ml-app-inference-secret"
    if secret_exists(namespace, inference_secret, client):
      logging.warning(f"Secret {namespace}/{inference_secret} already exists; "
                      f"Not recreating it.")
    else:
      postgres = _read_gcs_path("gs://issue-label-bot-dev_secrets/"
                                "issue-label-bot.postgres")
      webhook = _read_gcs_path(webhook_gcs)

      subprocess.check_call(["kubectl", "-n", namespace, "create",
                             "secret", "generic",
                             inference_secret,
                             f"--from-literal=DATABASE_URL={postgres}",
                             f"--from-literal=WEBHOOK_SECRET={webhook}"])


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(message)s|%(pathname)s|%(lineno)d|'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )

  fire.Fire(SecretCreator)
