import os
import logging
import json
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
import yaml
import random
from forward_utils import get_forwarded_repos
from forward_utils import publish_message
from forward_utils import create_topic_if_not_exists

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
prediction_threshold = defaultdict(lambda: .52)
prediction_threshold['question'] = .60

# set the project id and topic name for GCP pubsub
PUBSUB_PROJECT_ID = os.environ['GCP_PROJECT_ID']
PUBSUB_TOPIC_NAME = os.environ['GCP_PUBSUB_TOPIC_NAME']

# get repos that should possibly be forwarded
# dict: {repo_owner/repo_name: proportion}
forwarded_repos = get_forwarded_repos()

def init_issue_labeler():
    "Load all necessary artifacts to make predictions."
    title_pp_url = "https://storage.googleapis.com/codenet/issue_labels/issue_label_model_files/title_pp.dpkl"
    body_pp_url = 'https://storage.googleapis.com/codenet/issue_labels/issue_label_model_files/body_pp.dpkl'
    model_url = 'https://storage.googleapis.com/codenet/issue_labels/issue_label_model_files/Issue_Label_v1_best_model.hdf5'
    model_filename = 'downloaded_model.hdf5'


    with urlopen(title_pp_url) as f:
        title_pp = dpickle.load(f)

    with urlopen(body_pp_url) as f:
        body_pp = dpickle.load(f)

    model_path = get_file(fname=model_filename, origin=model_url)
    model = load_model(model_path)

    return IssueLabeler(body_text_preprocessor=body_pp,
                        title_text_preprocessor=title_pp,
                        model=model)

def init():
    "Load all necessary artifacts to make predictions."
    #save keyfile
    pem_string = os.getenv('PRIVATE_KEY')
    if not pem_string:
        raise ValueError('Environment variable PRIVATE_KEY was not supplied.')

    with open('private-key.pem', 'wb') as f:
        f.write(str.encode(pem_string))

    pubsub_json_string = os.getenv('PUBSUB_CREDENTIALS_JSON_BLOB')
    if not pubsub_json_string:
        raise ValueError('Environment variable PUBSUB_CREDENTIALS_JSON_BLOB was not supplied.')

    with open('pubsub-credentials.json', 'w') as f:
        # set GCP Auth per https://cloud.google.com/docs/authentication/getting-started
        json.dump(eval(pubsub_json_string), f)
        json_file_path = os.path.realpath(f.name)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_file_path

    app.graph = tf.get_default_graph()
    app.issue_labeler = init_issue_labeler()
    create_topic_if_not_exists(PUBSUB_PROJECT_ID, PUBSUB_TOPIC_NAME)

# this redirects http to https
# from https://stackoverflow.com/a/53501072/1518630
# @app.before_request
# def before_request():
#     if not request.is_secure and app.env != "development":
#         url = request.url.replace("http://", "https://", 1)
#         code = 301
#         return redirect(url, code=code)

# Webpage for app
@app.route("/", methods=["GET"])
def index():
    "Landing page"
    results = db.engine.execute("SELECT * FROM (SELECT distinct repo, username FROM issues a JOIN predictions b on a.issue_id=b.issue_id WHERE username != 'hamelsmu' LIMIT 200) as t ORDER BY random() LIMIT 25").fetchall()
    num_active_users = f'{db.engine.execute("SELECT count(distinct username) FROM issues").fetchall()[0][0]:,}'
    num_predictions = f'{db.engine.execute("SELECT count(*) FROM predictions").fetchall()[0][0]:,}'
    num_repos = f'{db.engine.execute("select count(*) from (select distinct username, repo from issues) as t").fetchall()[0][0]:,}'
    return render_template("index.html",
                           results=results,
                           num_active_users=num_active_users,
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

        try:
            # forward some issues of specific repos and select by their given forwarded proportion
            if f'{username}/{repo}' in forwarded_repos and random.random() <= forwarded_repos[f'{username}/{repo}']:
                # send the event to pubsub
                publish_message(PUBSUB_PROJECT_ID, PUBSUB_TOPIC_NAME,
                                installation_id, username, repo, issue_num)
                return f'Labeling of {username}/{repo}/issues/{issue_num} delegated to microservice via pubsub.'
        except Exception as e:
            LOG.error(e)

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

        # get the isssue handle
        issue = get_issue_handle(installation_id, username, repo, issue_num)


        labeled = True
        threshold = prediction_threshold[argmax]

        # take an action if the prediction is confident enough
        if (predictions[argmax] >= threshold):
            # initialize the label name to = the argmax
            label_name = argmax

            # handle the yaml file
            yaml = get_yaml(owner=username, repo=repo)
            if yaml and 'label-alias' in yaml:
                if  argmax in yaml['label-alias']:
                    LOG.warning('User has custom names: ', yaml['label-alias'])
                    new_name = yaml['label-alias'][argmax]
                    if new_name:
                        label_name = new_name

            # create message
            message = f'Issue-Label Bot is automatically applying the label `{label_name}` to this issue, with a confidence of {predictions[argmax]:.2f}. Please mark this comment with :thumbsup: or :thumbsdown: to give our bot feedback! \n\n Links: [app homepage](https://github.com/marketplace/issue-label-bot), [dashboard]({app_url}data/{username}/{repo}) and [code](https://github.com/hamelsmu/MLapp) for this bot.'
            # label the issue using the GitHub api
            issue.add_labels(label_name)
        
        else:
            message = f'Issue Label Bot is not confident enough to auto-label this issue. See [dashboard]({app_url}data/{username}/{repo}) for more details.'
            LOG.warning(f'Not confident enough to label this issue: # {str(issue_num)}')
            labeled = False
        
        # Make a comment using the GitHub api
        comment = issue.create_comment(message)

        # log the event to the database using ORM
        issue_db_obj.add_prediction(comment_id=comment.id,
                                    prediction=argmax,
                                    probability=predictions[argmax],
                                    logs=str(predictions),
                                    threshold=threshold, 
                                    labeled=labeled)
        return 'ok'
    return 'ok'

@app.route("/repos/<string:username>", methods=["GET"])
def get_repos(username):
    "Get repos actively installed in."
    ghapp = get_app()
    app = ghapp.get_app()
    try:
        install_id =  app.app_installation_for_user(f'{username}').id
    except:
        return f'No current installations for {username} found.'
    
    url = f'https://api.github.com/installation/repositories'
    headers = {'Authorization': f'token {ghapp.get_installation_access_token(install_id)}',
               'Accept': 'application/vnd.github.machine-man-preview+json'}
    
    response = requests.get(url=url, headers=headers, params={'per_page':100})
    if response.status_code == 200:
        repos = response.json()['repositories']
        repos_with_preds = [x.repo for x in Issues.query.filter(Issues.username == username and Issues.predictions != None).distinct(Issues.repo).all()]
        return render_template('repos.html', repos=repos, username=username, repos_with_preds=repos_with_preds)
    
    else:
        return response.status_code
        
@app.route('/users')
def show_users():
    users = get_users()
    users_with_preds = [x.username for x in Issues.query.filter(Issues.predictions != None).distinct(Issues.username).all()]

    users = [{'name':a, 'is_pred':b} for a,b in sorted([(x, x in users_with_preds) for x in users], key=lambda x: ~x[1])]

    return render_template('users.html', users=users, users_with_preds=users_with_preds)

@app.route("/data/<string:owner>/<string:repo>", methods=["GET", "POST"])
def data(owner, repo):
    "Route where users can see the Bot's recent predictions for a repo"
    installed = app_installation_exists(owner=owner, repo=repo)
    alert = None
    if not installed:
        alert = 'Warning: The app is no longer installed on this repo. Will not be able to update feedback, but you can still view predictions.'

    if not is_public(owner, repo):
        return render_template("data.html",
                               results=[],
                               num_issues=0,
                               owner=owner,
                               repo=repo,
                               is_public=False,
                               error=f'<span style="font-weight:bold">{owner}/{repo}</span> is a private repo or does not exist.')

    issues = Issues.query.filter(Issues.username == owner, Issues.repo == repo).all()
    issue_numbers = [x.issue_id for x in issues]

    if request.method == 'POST':
        if installed:
            update_feedback(owner=owner, repo=repo)
        else:
            return render_template("data.html",
                               results=[],
                               num_issues=0,
                               owner=owner,
                               repo=repo,
                               is_public=True,
                               error=f'App is no longer installed for <span style="font-weight:bold">{owner}/{repo}</span>. Cannot fetch feedback.')

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
                           repo=repo,
                           alert=alert,
                           is_public=True,
                           installed=installed)

@app.route("/health_check", methods=["GET"])
def health_check():
    "route for load balancer."
    return jsonify({'success':True}), 200, {'ContentType':'application/json'}

def update_feedback(owner, repo):
    "Update feedback for predicted labels for an owner/repo"
    # authenticate webhook to make sure it is from GitHub
    issues = Issues.query.filter(Issues.username == owner, Issues.repo == repo).order_by(Issues.issue_num.desc()).limit(50).all()
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
        try:
            reactions = ghapp.get_reactions(owner=owner,
                                            repo=repo,
                                            comment_id=prediction.comment_id,
                                            iat=installation_access_token)
            prediction.likes = reactions['+1']
            prediction.dislikes = reactions['-1']
        except:
            continue
    db.session.commit()
    print(f'Successfully updated feedback based on reactions for {len(predictions)} predictions in {owner}/{repo}.')


def get_app():
    "grab a fresh instance of the app handle."
    app_id = os.getenv('APP_ID')
    key_file_path = 'private-key.pem'
    ghapp = GitHubApp(pem_path=key_file_path, app_id=app_id)
    return ghapp

def get_users():
    "git list of users."
    ghapp = get_app()
    app = ghapp.get_app()
    return [x.account['login'] for x in list(app.app_installations())]

def app_installation_exists(owner, repo):
    "check if app is installed on the repo."
    ghapp = get_app()
    try:
        ghapp.get_installation_id(owner=owner, repo=repo)
        return True
    except:
        return False

def get_issue_handle(installation_id, username, repository, number):
    "get an issue object."
    ghapp = get_app()
    install = ghapp.get_installation(installation_id)
    return install.issue(username, repository, number)

def get_yaml(owner, repo):
    """
    Looks for the yaml file in a /.github directory.
    
    yaml file must be named issue_label_bot.yaml
    """
    ghapp = get_app()
    try:
        # get the app installation handle
        inst_id = ghapp.get_installation_id(owner=owner, repo=repo)
        inst = ghapp.get_installation(installation_id=inst_id)
        # get the repo handle, which allows you got get the file contents
        repo = inst.repository(owner=owner, repository=repo)
        results = repo.file_contents('.github/issue_label_bot.yaml').decoded
    
    except:
        return None
    
    return yaml.safe_load(results)

def verify_webhook(request):
    "Make sure request is from GitHub.com"

    # if we are testing, don't bother checking the payload
    if os.getenv('DEVELOPMENT_FLAG'): return True

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
