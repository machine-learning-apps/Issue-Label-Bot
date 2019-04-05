[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)

[blog]: https://www.google.com/

Code for Medium article: ["How to create machine learning products that automate tasks on GitHub for fun and profit"][blog]

# Issue-Label Bot

A [GitHub App](https://developer.github.com/apps/) powered by machine learning, written in python.  A detailed discussion behind the motivation for this app and an explanation of the components are located in the [blog article][blog] mentioned above.

### Links

 - GitHub home page For [Issue-Label Bot](https://github.com/apps/issue-label-bot), where you can install the app. (See disclaimers below before installing).
 - [Prediction Dashboard](http://mlbot.net:3000/): examples of label predictions for issues.
 
### Table of Contents
 
 - [/notebooks](/notebooks): contains notebooks on how to train the model and interact with the GitHub api uing a python client.
 - [/flask_app](/flask_app): code for a flask app that listens for [GitHub issue events](https://developer.github.com/v3/issues/events/) and responds with predictions.  This is the main application that the user will interact with.
- [/argo](/argo): the code in this directory relates to the construction of [Argo ML Pipelines](https://argoproj.github.io/) for training and deploying ML workflows. 
- [Dockerfile](/Dockerfile): this is the container that is used to run the flask app.  The build for this container is hosted on DockerHub at [hamelsmu/mlapp](https://hub.docker.com/r/hamelsmu/mlapp).
- [heroku.yml](/heroku.yml): this is used for [deploying to Heroku](https://devcenter.heroku.com/articles/container-registry-and-runtime).
- {[deployments](/deployments.yaml), [service](/service.yaml), [fake-secret](/fake-secret.yaml)}.yaml: these files relate to a Kubernetees deployment.
- 

### Deployment
The assets in this repo allow you to deploy to [Heroku](https://devcenter.heroku.com/articles/container-registry-and-runtime) (easier) or a Kubernetees cluster (more advanced).  There are several environment variables that you must pass to the flask app if you wish to run the app:

1. `PRIVATE_KEY`:  this is the private key you use to [authenticate as an app](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment) with the GitHub api.
2. `DATABASE_URL`: this is the URL that contains the login information for your POSTGRESQL database, usually in the form: `postgres://<username>:<password>@<url>:5432/<database_name>`
3. `APP_ID`: this is a unique identifier provided to you by GitHub when you [register your app](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment).
4. `FLASK_ENV`: this is usually set to either `production` or `development`, you only want to use `deployment` for local testing.
5. `PORT`: this is the port your app will be serving on.  Note that if you are deploying to Heroku, Heroku will override this variable with their own value when building your app.
6. `APP_URL`: this is the url for the homepage of your app.  This allows you to switch domains etc. as necessary.

In Heroku, secrets can be passed in as [configuration variables](https://devcenter.heroku.com/articles/config-vars).  Furthermore, [this documentation](https://kubernetes.io/docs/concepts/configuration/secret/#creating-a-secret-manually) describes how you can set secrets in Kubernetees.

### Disclaimers

[Issue-Label Bot](https://github.com/apps/issue-label-bot) is for educational and demonstration purposes only.  Do not install this application on any repositories that contain sensitive information. This application may be discontinued at any time without warning.
