[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) [![License: MIT](https://img.shields.io/badge/License-MIT-darkgreen.svg)](https://opensource.org/licenses/MIT)
[![Powered-By-Fast-AI](https://img.shields.io/badge/fastai%20v1.5.3%20%20-blueviolet.svg?logo=github)](https://github.com/fastai/fastai/tree/69231e6026b7fcbe5b67ab4eaa23d19be3ea0659)
[![Weights-And-Biases](https://img.shields.io/badge/Weights%20&%20Biases-black.svg?logo=google-analytics)](https://app.wandb.ai/github/issues_lang_model)

# A Language Model Trained On 16M+ GitHub Issues For Transfer Learning

**Motivation:**  [Issue Label Bot](https://github.com/machine-learning-apps/Issue-Label-Bot) predicts 3 generic issue labels: `bug`, `feature request` and `question`.  However, it would be nice to predict personalized issue labels instead of generic ones.  To accomplish this, we can use the issues that are already labeled in a repository as training data for a model that can predict personalized issue labels.  One challenge with this approach is there is often a small number of labeled issues in each repository.  In order to mitigate this concern, we utilize [transfer-learning](http://nlp.fast.ai/) by training a language trained over 16 million GitHub Issues and fine-tune this to predict issue labels.

# End-Product: An API that returns embeddings from GitHub Issue Text.

The manifest files in [/deployment](/deployment) define a service that will return 2400 dimensional embeddings given the text of an issue.  The api endpoints are hosted on https://gh-issue-labeler.com/

All routes expect `POST` requests with a header containing a `Token` field. Below is  a list of endpoints:

1. `https://embeddings.gh-issue-labeler.com/text`:  expects a json payload of `title` and `body` and returns a single 2,400 dimensional vector that represents latent features of the text. For example, this is how you would interact with this endpoint from python:

    ```python
    import requests
    import json
    import numpy as np
    from passlib.apps import custom_app_context as pwd_context

    API_ENDPOINT = 'https://embeddings.gh-issue-labeler.com/text'
    API_KEY = 'YOUR_API_KEY' # Contact maintainers to get this

    # A toy example of a GitHub Issue title and body
    data = {'title': 'Fix the issue', 
            'body': 'I am encountering an error\n when trying to push the button.'}

    # sending post request and saving response as response object 
    r = requests.post(url=API_ENDPOINT,
                    headers={'Token':pwd_context.hash(API_KEY)},
                    json=data)

    # convert string back into a numpy array
    embeddings = np.frombuffer(r.content, dtype='<f4')
    ```



2. `https://embeddings.gh-issue-labeler.com//all_issues/<owner>/<repo>` :construction: this will return a numpy array of the shape (# of labeled issues in repo, 2400), as well a list of all the labels for each issue.  This endpoint is still under construction.

# Training the Language Model

The language model is built with the [fastai](http://nlp.fast.ai/) library.  The [notebooks](/notebooks) folder contains a tutorial of the steps you need to build a language model:

1. [01_AcquireData.ipynb](/notebooks/01_AcquireData.ipynb): Describes how to acquire and pre-process the data using [mdparse](https://github.com/machine-learning-apps/mdparse), which parses and annotates markdown files.
2. [02_fastai_DataBunch.ipynb](/notebooks/02_fastai_DataBunch.ipynb):  The fastai library uses an object called a [Databunch](https://docs.fast.ai/basic_data.html#DataBunch) around pytorch's dataloader class to encapuslate additional metadata and functionality.  This notebook walks through the steps of preparing this data structure which will be used by the model for training.
3. [03_Create_Model.ipynb](/notebooks/03_Create_Model.ipynb): This walks through the process of instantiating the fastai language model, along with callbacks for early stopping, logging and saving of artifacts.  Additionally, this notebook illustrates how to train the model.
4. [04_Inference.ipynb](/notebooks/04_Inference.ipynb): shows how to use the language model to perform inference in order to extract latent features in the form of a 2,400 dimension vector from GitHub Issue text. This notebook shows how to load the Databunch and model and save only the model for inference.  [/flask_app/inference.py](/flask_app/inference.py) contains utilities that makes the inference process easier.

### Putting it all together: hyper-parameter tuning

The [hyperparam_sweep](/hyperparam_sweep) folder contains [lm_tune.py](/hyperparam_sweep/lm_tune.py) which is a script used to train the model.  Most importantly, we use this script in conjuction with [hyper-parameter sweeps in Weights & Biases](https://docs.wandb.com/docs/sweep.html)

We were able to try 538 different hyper-paramter combinations using Bayesian and random grid search concurrently to choose the best model:

![](/hyperparam_sweep/images/parallel_coordinates.png)

The hyperparameter tuning process is described in greater detail in the [hyperparam_sweep](/hyperparam_sweep) folder.

# Files
 
 - [/notebooks](/notebooks): contains notebooks on how to gather and clean the data and train the language model.
 - [/hyperparam_sweep](/hyperparam_sweep): this folder contains instructions on doing a hyper-parameter sweep with [Weights & Biases](https://www.wandb.com).
 - [/flask_app](/flask_app): code for a flask app that is the API that listens for POST requests. 
 - [/script](/script): this directory contains the entry point for running the REST API server that end users will interface with:
    - [dev](/script/dev): this bash script pulls the necessary docker images and starts the API server.
    - [bootstrap](/script/bootstrap): this re-builds the docker image and pushes it to Dockerhub.  It is necessary to re-build the container anytime the code for the flask app or language model is updated.
- [/deployment](/deployment): This directory contains files that are helpful in deploying the app.
    - [Dockerfile](/deployment/Dockerfile) this is the definition of the container that is used to run the flask app.  The build for this container is hosted on DockerHub at [hamelsmu/issuefeatures-api-cpu](https://hub.docker.com/r/hamelsmu/issuefeatures-api-cpu).
    - *.yaml: these files relate to a Kubernetees deployment.


# Appendix: Location of Language Model Artifacts

### Google Cloud Storage

- **model for inference** (965 MB): https://storage.googleapis.com/issue_label_bot/model/lang_model/models_22zkdqlr/trained_model_22zkdqlr.pkl


- **encoder (for fine-tuning w/a classifier)** (965 MB): 
https://storage.googleapis.com/issue_label_bot/model/lang_model/models_22zkdqlr/trained_model_encoder_22zkdqlr.pth


- **fastai.databunch** (27.1 GB):
https://storage.googleapis.com/issue_label_bot/model/lang_model/data_save.pkl


- **checkpointed model** (2.29 GB): 
https://storage.googleapis.com/issue_label_bot/model/lang_model/models_22zkdqlr/best_22zkdqlr.pth

### Weights & Biases Run

https://app.wandb.ai/github/issues_lang_model/runs/22zkdqlr/overview
