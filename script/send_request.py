"""A helper script to send requests to test the label bot."""
import base64
import fire
import hmac
import json
import logging
import requests
import subprocess

class SendRequest:
  @staticmethod
  def send(url="https://label-bot-dev.mlbot.net/event_handler"):
    # Get the webhook secret
    secret = subprocess.check_output(["kubectl", "get", "secret",
                                      "ml-app-inference-secret",
                                      "-o", "jsonpath='{.data.WEBHOOK_SECRET}'"])

    secret_decoded = base64.b64decode(secret).decode()

    if url != "https://label-bot-dev.mlbot.net/event_handler":
      logging.error("You aren't using the dev label bot webhook but "
                    "send_request.py currently hard codes the GitHub App "
                    "Install ID to kf-label-bot-dev on kubeflow/code-intelligence "
                    "we need to change that in order to be able to allow "
                    "worker to actually write to the repo.")
    # TODO(jlewi): We should allow specificing a specific issue.
    payload = {
      "action": "opened",
      # Installation corresponding to kf-label-bot-dev on
      # kubeflow/code-intelligence
      "installation": {
        # TODO(jlewi): This is the installation id of the kf-label-bot-dev
        "id": 5980888,
      },
      "issue": {
        "number": 104,
        "title": "Test kf-label bot-dev this is a bug",
        "body": ("Test whether events are correctly routed to the dev instance."
                 "If not then there is a bug in the setup")
      },
      "repository": {
        "full_name": "kubeflow/code-intelligence",
        "private": False,
      }
    }

    data = str.encode(json.dumps(payload))
    # See: https://developer.github.com/webhooks/securing/
    # We need to compute the signature of the payload using the secret
    mac = hmac.new(str.encode(secret_decoded), msg=data, digestmod='sha1')

    headers = {
     "X-Hub-Signature": "=" + mac.hexdigest(),
     "Content-Type": "application/json",
    }

    # We use data and not json because we need to compute the hash of the
    # data to match the signature
    logging.info(f"Send url: {url}")
    response = requests.post(url, data=data, headers=headers)

    logging.info(f"Response {response}")

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(message)s|%(pathname)s|%(lineno)d|'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )

  fire.Fire(SendRequest)

