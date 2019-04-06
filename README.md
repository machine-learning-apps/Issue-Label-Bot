[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)


[blog]: https://www.google.com/

### Code for: ["How to automate tasks on GitHub for fun and profit with machine learning"][blog]

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->
Table of Contents

- [Issue-Label Bot](#issue-label-bot)
	- [Important links](#important-links)
	- [Files](#files)
- [Running This Code](#running-this-code)
	- [Environment Variables](#environment-variables)
	- [Run Locally](#run-locally)
	- [Deploy As A Service](#deploy-as-a-service)
- [Contributing](#contributing)
	- [Roadmap](#roadmap)
	- [References](#references)
- [Disclaimers](#disclaimers)

<!-- /TOC -->

# Issue-Label Bot

A [GitHub App](https://developer.github.com/apps/) powered by machine learning, written in python.  A discussion of the motivation and the overall process of building this app is available in this [blog article][blog].

Original Authors: [@hamelsmu](https://github.com/hamelsmu), [@inc0](https://github.com/inc0)

## Important links

 - GitHub home page For [Issue-Label Bot](https://github.com/apps/issue-label-bot), where you can install the app. See [disclaimers](#Disclaimers) below before installing).
 - [Prediction Dashboard](http://mlbot.net:3000/): examples of label predictions for issues.
 
## Files
 
 - [/notebooks](/notebooks): contains notebooks on how to train the model and interact with the GitHub api uing a python client.
 - [/flask_app](/flask_app): code for a flask app that listens for [GitHub issue events](https://developer.github.com/v3/issues/events/) and responds with predictions.  This is the main application that the user will interact with.
- [/argo](/argo): the code in this directory relates to the construction of [Argo ML Pipelines](https://argoproj.github.io/) for training and deploying ML workflows. 
- [/deployment](/deployment): This directory contains files that are helpful in deploying the app.
    - [Dockerfile](/deployment/Dockerfile) this is the definition of the container that is used to run the flask app.  The build for this container is hosted on DockerHub at [hamelsmu/mlapp](https://hub.docker.com/r/hamelsmu/mlapp).
    - [heroku.yml](/heroku.yml): this is used for [deploying to Heroku](https://devcenter.heroku.com/articles/container-registry-and-runtime).
    - *.yaml: these files relate to a Kubernetees deployment.
 
# Running This Code

 ## Prerequisites

To utilize the code in this repository, you will need to register a GitHub App of your own and install this app on your desired repositories and store authentication secrets.  

First, walk through the [prerequisites section of this getting started guide](https://developer.github.com/apps/quickstart-guides/using-the-github-api-in-your-app/#prerequisites) **except** The Ruby programming language" section as we will be using python instead as the client that interfaces with the GitHub api.  

 Second, [setup your development environment](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment/). Make sure you create a Webhook secret, even though this step is optional.

 Next, setup a postgres database.  You can do this [for free on Heroku](https://elements.heroku.com/addons/heroku-postgresql).    Detailed instructions (stolen shamelessly from [here](https://www.edx.org/course/cs50s-web-programming-with-python-and-javascript)):

1. Navigate to https://www.heroku.com/, and create an account if you don’t already have one.
2. On Heroku’s Dashboard, click “New” and choose “Create new app.”
3. Give your app a name, and click “Create app.”
4. On your app’s “Overview” page, click the “Configure Add-ons” button.
5. In the “Add-ons” section of the page, type in and select “Heroku Postgres.”
6. Choose the “Hobby Dev - Free” plan, which will give you access to a free PostgreSQL database that will support up to 10,000 rows of data. Click “Provision.”
7. Now, click the “Heroku Postgres :: Database” link.
8. You should now be on your database’s overview page. Click on 8 “Settings”, and then “View Credentials.” This is the information you’ll need to log into your database.

Finally, you need to create environment variables for all the secrets, which is described below.     

## Environment Variables

1. `PRIVATE_KEY`:  this is the private key you use to [authenticate as an app](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment) with the GitHub api.
2. `WEBHOOK_SECRET`: this is used to verify that payloads received by your app are actually from GitHub.  This is described [here](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment/).
2. `DATABASE_URL`: this is the URL that contains the login information for your POSTGRESQL database, usually in the form: `postgres://<username>:<password>@<url>:5432/<database_name>`
3. `APP_ID`: this is a unique identifier provided to you by GitHub when you [register your app](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment).
4. `FLASK_ENV`: this is usually set to either `production` or `development`.  You will want to use `deployment` for local testing.
5. `PORT`: this is the port your app will be serving on.  Note that if you are deploying to Heroku, Heroku will override this variable with their own value when building your app.  For local development, you will want this to match the [port Smee is serving to](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment/#step-1-start-a-new-smee-channel).
6. `APP_URL`: this is the url for the homepage of your app that is provided to users as a link in issue comments.  You can set this to an arbitrary value for local development.

Note: If you are using [zsh](http://www.zsh.org/), the [dotenv](https://github.com/robbyrussell/oh-my-zsh/tree/master/plugins/dotenv) plugin can be useful for managing environment variables.

## Run Locally

1. **Install Dependencies**: Install [requirements.txt](/requirements.txt) into a virtual environment.  If you are using [pipenv](https://pipenv.readthedocs.io/en/latest/) install the necessary dependencies from [Pipfile.lock](/Pipenv.lock) by typing `pipenv install` in the root of this repository.

2. **Run the flask app**: run `python flask_app/app.py` from the root of this repository.  For this to work, you must correctly set the environment variables as described in the [Environment Variables](#Environment-Variables) section.

3. Optional - **Run app as docker container**.  A Docker container that serves [Issue-Label Bot](https://github.com/apps/issue-label-bot) can be built with the command `bash script/bootstrap` from the root of this repository.  This script builds a Docker image named `hamelsmu/mlapp`, which is also available [on Dockerhub](https://hub.docker.com/r/hamelsmu/mlapp).  If you desire to run the Docker container locally for testing, you must [pass the necessary environment variables](https://stackoverflow.com/questions/30494050/how-do-i-pass-environment-variables-to-docker-containers) to the Docker container at runtime, as well as expose necessary ports for the app. See the [References](#References) section for more resources on using Docker.


## Deploy As A Service

The assets in this repo allow you to [deploy to Heroku](https://devcenter.heroku.com/articles/container-registry-and-runtime) (easier) or a Kubernetees cluster (more advanced).  

In Heroku, secrets can be passed in as [configuration variables](https://devcenter.heroku.com/articles/config-vars).  Furthermore, [this documentation](https://kubernetes.io/docs/concepts/configuration/secret/#creating-a-secret-manually) describes how you can set secrets in Kubernetees.  Make sure you set the environment variable `FLASK_ENV` to `production` if you are going to deploy the app publicly.


# Contributing

We welcome all forms of contributions.  We are especially interested in the following:

- Bug fixes
- Enhancements or additional features
- Improvements to the model, or expansion of the dataset(s) used for training.  

## Roadmap

The authors of this project are interested in adding the following features in the near future:

- Using the tools from [fastai](https://docs.fast.ai/) to explore:
    - State of the art architectures, such as [Multi-Head Attention](https://docs.fast.ai/text.models.html#MultiHeadAttention)
    - Pre-training on a large corpus such as stack overflow and fine tuning that on GitHub issues to predict repo-specific issue labels.  A related project that can help bootstrap this task is [stackroboflow.com](https://stackroboflow.com/about/index.html)
- Using [GitHub Actions](https://github.com/features/actions) to trigger automated deploys of this code.
- Model training and pipeline orchestration on [Argo pipelines](https://argoproj.github.io/).


## References
 - The code in this repo and associated tutorial(s) assume familiarity with Docker. [This blog post](https://towardsdatascience.com/how-docker-can-help-you-become-a-more-effective-data-scientist-7fc048ef91d5) offers a gentle introduction to Docker for data scientists.
 
 - Need inspiration for other data products you can build using machine learning and public GitHub datasets?  See these examples:
    - [GitHub issue summarization](https://towardsdatascience.com/how-to-create-data-products-that-are-magical-using-sequence-to-sequence-models-703f86a231f8) and recommendation.
    - Natural language [semantic code search](https://towardsdatascience.com/semantic-code-search-3cd6d244a39c).
- My favorite course on flask: [HarvardX CS50 Web](https://www.edx.org/course/cs50s-web-programming-with-python-and-javascript).
- My favorite MOOCs by [fastai](https://www.fast.ai/) for [machine learning](http://course18.fast.ai/ml) and [deep learning](http://course.fast.ai/).

# Disclaimers

[Issue-Label Bot](https://github.com/apps/issue-label-bot) is for educational and demonstration purposes only.  Furthermore, **this app only works on public repositories and will do nothing if installed on a private repo.**
