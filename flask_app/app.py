import os
import logging
from collections import defaultdict
import hmac
from flask import (abort, Flask, session, render_template, 
                   session, redirect, url_for, request,
                   flash, jsonify)
from flask_session import Session
from sqlalchemy import desc
from mlapp import GitHubApp
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import get_file
from utils import IssueLabeler
import dill as dpickle
from urllib.request import urlopen
from sql_models import db, Issues, Predictions
import tensorflow as tf
import requests
import ipdb

app = Flask(__name__)
app_url = os.getenv('APP_URL')

# Configure session to use filesystem. Hamel: BOILERPLATE.
app.config["SESSION_PERMANENT"] = False
Session(app)

# Bind database to flask app
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Additional Setup inspired by https://github.com/bradshjg/flask-githubapp/blob/master/flask_githubapp/core.py
app.webhook_secret = os.getenv('WEBHOOK_SECRET')
LOG = logging.getLogger(__name__)    

# set the prediction threshold for everything except for the label question which has a different threshold
prediction_threshold = defaultdict(lambda: .55)
prediction_threshold['question'] = .65


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
@app.route("/", methods=["GET"])
def index():
    "Landing page"
    results = db.engine.execute("SELECT * FROM (SELECT distinct repo, username FROM issues a JOIN predictions b on a.issue_id=b.issue_id) as t ORDER BY random() LIMIT 50").fetchall()
    num_users = f'{len(db.engine.execute("SELECT distinct username FROM issues").fetchall()):,}'
    num_predictions = f'{db.engine.execute("SELECT count(*) FROM predictions").fetchall()[0][0]:,}'
    num_repos = f'{len(results):,}'
    return render_template("index.html", 
                           results=results, 
                           num_users=num_users, 
                           num_repos=num_repos,
                           num_predictions=num_predictions)

# smee by default sends things to /event_handler route
@app.route("/event_handler", methods=["POST"])
def bot():
    "Handle payload"
    # authenticate webhook to make sure it is from GitHub
    verify_webhook(request)

    # Check if payload corresponds to an issue being opened
    if 'action' in request.json and request.json['action'] == 'opened' and ('issue' in request.json):
        # get metadata
        installation_id = request.json['installation']['id']
        issue_num = request.json['issue']['number']
        private = request.json['repository']['private']
        username, repo = request.json['repository']['full_name'].split('/')
        title = request.json['issue']['title']
        body = request.json['issue']['body']

        # don't do anything if repo is private.
        if private:
            return 'ok'

        # write the issue to the database using ORM
        issue_db_obj = Issues(repo=repo,
                              username=username,
                              issue_num=issue_num,
                              title=title,
                              body=body)
        
        db.session.add(issue_db_obj)
        db.session.commit()
        
        # make predictions with the model
        with app.graph.as_default():
            predictions = app.issue_labeler.get_probabilities(body=body, title=title)
        #log to console
        LOG.warning(f'issue opened by {username} in {repo} #{issue_num}: {title} \nbody:\n {body}\n')
        LOG.warning(f'predictions: {str(predictions)}')

        # get the most confident prediction
        argmax = max(predictions, key=predictions.get)
        # take an action if the prediction is confident enough
        if predictions and (predictions[argmax] >= prediction_threshold[argmax]):
            # create message
            message = f'Issue-Label Bot is automatically applying the label `{argmax}` to this issue, with a confidence of {predictions[argmax]:.2f}. Please mark this comment with :thumbsup: or :thumbsdown: to give our bot feedback! \n\n Links: [dashboard]({app_url}data/{username}/{repo}), [app homepage](https://github.com/apps/issue-label-bot) and [code](https://github.com/hamelsmu/MLapp) for this bot.'
            # label the issue and make a comment using the GitHub api
            issue = get_issue_handle(installation_id, username, repo, issue_num)
            comment = issue.create_comment(message)
            issue.add_labels(argmax)

            # log the prediction to the database using ORM
            issue_db_obj.add_prediction(comment_id=comment.id,
                                        prediction=argmax,
                                        probability=predictions[argmax],
                                        logs=str(predictions))
            return 'ok'

    else:
        return 'ok'

@app.route("/data/<string:owner>/<string:repo>", methods=["GET", "POST"])
def data(owner, repo):
    "Route where users can see the Bot's recent predictions for a repo"

    if not is_public(owner, repo):
        return render_template("data.html",
                               results=[],
                               owner=owner,
                               repo=repo,
                               error=f'<span style="font-weight:bold">{owner}/{repo}</span> is a private repo or does not exist.')

    issues = Issues.query.filter(Issues.username == owner, Issues.repo == repo).all()
    issue_numbers = [x.issue_id for x in issues]

    if request.method == 'POST':
        update_feedback(owner=owner, repo=repo)

    # get the 50 most recent predictions.
    predictions = (Predictions.query.filter(Predictions.issue_id.in_(issue_numbers))
                    .order_by(desc(Predictions.issue_id))
                    .limit(50)
                    .all())

    num_issues = len(issues)
    num_predictions = len(predictions)
    
    return render_template("data.html",
                           results=predictions,
                           num_issues=num_issues,
                           num_predictions=num_predictions,
                           owner=owner,
                           repo=repo)


def update_feedback(owner, repo):
    "Update feedback for predicted labels for an owner/repo"
    # authenticate webhook to make sure it is from GitHub
    issues = Issues.query.filter(Issues.username == owner, Issues.repo == repo).all()
    issue_numbers = [x.issue_id for x in issues]

    # only update last 100 things to prevent edge cases on repos with large number of issues.
    predictions = (Predictions.query.filter(Predictions.issue_id.in_(issue_numbers))
                   .limit(100)
                   .all())

    # we only want to get the installation token once for the list of predictions.
    ghapp = get_app()
    installation_id = ghapp.get_installation_id(owner=owner, repo=repo)
    installation_access_token = ghapp.get_installation_access_token(installation_id)

    # grab all the reactions and update the statistics in the database.
    for prediction in predictions:
        reactions = ghapp.get_reactions(owner=owner, 
                                        repo=repo, 
                                        comment_id=prediction.comment_id,
                                        iat=installation_access_token)
        prediction.likes = reactions['+1']
        prediction.dislikes = reactions['-1']
    db.session.commit()
    print(f'Successfully updated feedback based on reactions for {len(predictions)} predictions in {owner}/{repo}.')


def get_app():
    "grab a fresh instance of the app handle."
    app_id = os.getenv('APP_ID')
    key_file_path = 'private-key.pem'
    ghapp = GitHubApp(pem_path=key_file_path, app_id=app_id)
    return ghapp

def get_issue_handle(installation_id, username, repository, number):
    "get an issue object."
    ghapp = get_app()
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

def is_public(owner, repo):
    "Verify repo is public."
    try:
        return requests.head(f'https://github.com/{owner}/{repo}').status_code == 200
    except:
        return False

if __name__ == "__main__":
    init()
    with app.app_context():
        # create tables if they do not exist
        db.create_all()

    # make sure things reload
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True, host='0.0.0.0', port=os.getenv('PORT'))