import os
import logging
import hmac
from flask import (abort, Flask, session, render_template, 
                   session, redirect, url_for, request,
                   flash, jsonify)
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from mlapp import GitHubApp
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import get_file
from utils import IssueLabeler
import dill as dpickle
from urllib.request import urlopen
import tensorflow as tf
import ipdb

app = Flask(__name__)

# Configure session to use filesystem. Hamel: BOILERPLATE.
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Additional Setup inspired by https://github.com/bradshjg/flask-githubapp/blob/master/flask_githubapp/core.py
app.webhook_secret = os.getenv('WEBHOOK_SECRET')
LOG = logging.getLogger(__name__)

def init():
    "Load all necessary artifacts to make predictions."
    title_pp_url = "https://storage.googleapis.com/codenet/issue_labels/issue_label_model_files/title_pp.dpkl"
    body_pp_url = 'https://storage.googleapis.com/codenet/issue_labels/issue_label_model_files/body_pp.dpkl'
    model_url = 'https://storage.googleapis.com/codenet/issue_labels/issue_label_model_files/Issue_Label_v1_best_model.hdf5'
    model_filename = 'downloaded_model.hdf5'

    #save keyfile
    pem_string = os.getenv('PRIVATE_KEY')
    if not pem_string:
        raise ValueError('Environment variable PRIVATE_KEY was not supplied.')
    
    with open('private-key.pem', 'wb') as f:
        f.write(str.encode(pem_string))

    with urlopen(title_pp_url) as f:
        title_pp = dpickle.load(f)

    with urlopen(body_pp_url) as f:
        body_pp = dpickle.load(f)
    
    model_path = get_file(fname=model_filename, origin=model_url)
    model = load_model(model_path)
    app.graph = tf.get_default_graph()
    app.issue_labeler = IssueLabeler(body_text_preprocessor=body_pp,
                                     title_text_preprocessor=title_pp,
                                     model=model)


# smee by default sends things to /event_handler route
@app.route("/event_handler", methods=["POST", "GET"])
def index():
    "Handle payload"
    # authenticate webhook to make sure it is from GitHub
    verify_webhook(request)

    # if user tries to login, try to authenticate them using naive approach.
    payload = request.json
    # Check if payload corresponds to open issue
    if request.json['action'] == 'opened' and ('issue' in request.json):
        # get metadata
        installation_id = request.json['installation']['id']
        issue_id = request.json['issue']['number']
        username, repo = request.json['repository']['full_name'].split('/')
        title = request.json['issue']['title']
        body = request.json['issue']['body']

        with app.graph.as_default():
            predictions = app.issue_labeler.get_probabilities(body=body, title=title)
        #log to console
        print(f'issue opened by {username} in {repo} #{issue_id}: {title} \nbody:\n {body}\n')
        print(f'predictions: {str(predictions)}')

        label = None
        for key in predictions:
            if predictions[key] >= 0.6:
                label = key
                # create message
                message = f'KFlow-bot has determined with {predictions[key]:.2f} probability that this issue should be labeled as `{key}` and is auto-labeling this issue. Please mark this comment with :thumbsup: or :thumbsdown: to give our bot feedback!'

                issue = get_issue_handle(installation_id, username, repo, issue_id)
                issue.create_comment(message)
                issue.add_labels(label)

    else:
        pass
    return 'ok'

def get_issue_handle(installation_id, username, repository, number):
    app_id = 27079
    key_file_path = 'private-key.pem'
    ghapp = GitHubApp(pem_path=key_file_path, app_id=app_id)
    install = ghapp.get_installation(installation_id)
    return install.issue(username, repository, number)

def verify_webhook(request):
    "Make sure request is from GitHub.com"
    # Inspired by https://github.com/bradshjg/flask-githubapp/blob/master/flask_githubapp/core.py#L191-L198
    signature = request.headers['X-Hub-Signature'].split('=')[1]

    mac = hmac.new(str.encode(app.webhook_secret), msg=request.data, digestmod='sha1')

    if not hmac.compare_digest(mac.hexdigest(), signature):
        LOG.warning('GitHub hook signature verification failed.')
        abort(400)


if __name__ == "__main__":
    #app.run(debug=True, host='0.0.0.0', port=os.getenv('PORT'))
    init()
    app.run(debug=True, host='0.0.0.0', port=os.getenv('PORT'))

