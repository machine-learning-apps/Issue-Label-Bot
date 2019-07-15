# Fairing and MLApp

We will use fairing and Seldon to deploy our model on Kubeflow.

[fairing](https://github.com/kubeflow/fairing/tree/master/fairing) is a python
SDK that makes it super easy to 

  * Build Docker images from notebooks and python files
  * Create Kubernetes deployments and services to deploy your model.

[Seldon](https://github.com/SeldonIO/seldon-core) provides a platform for deploying
models on Kubernetes.

fairing uses seldon to wrap your python functions in a model server that can handle
REST or gRPC calls.

Below are instructions for deploying your model using fairing.

Fairing is a python library so it can be used in notebooks or from python modules
invoked via the python interpreter.

This example will use notebooks running inside your Kubeflow cluster but 
you could just as easily run fairing in your favorite IDE on your local 
machine and still deploy on your Kubeflow cluster.


## Create a base image

We need to create a suitable Docker image to use as our base image.

We will run this step on your local machine using Docker.

We could also use Kaniko and the ClusterBuilder inside fairing to run this
inside your Kubeflow cluster.

We could build a complete Docker image every time our code changes but this
would be rather slow since installing dependencies like pandas can be expensive.

So instead we build a base Docker image which contains our dependencies and
then just create a new image by adding our code to this image.

Run the following command to build and push your image

```
IMG=<Registry URI for the image>
IMG=${IMG} make push
```

Set IMG to URI you want to host the image in your docker registry.

On Google Cloud Platform we can use GCR and set the URI to

```
IMG=gcr.io/${PROJECT}/mlapp/base
```

  * Substitute your GCP project id for PROJECT

On GCP you may need to run the following gcloud command to provide docker with credentials for your GCP project

```
gcloud auth configure docker
```

You can also use GCB to build the image. This can be much faster because we avoid pulling/pushing the base image over our local network which can be quite large

```
PROJECT=${PROJECT} IMG=${IMG} make build-gcb
```

## Start a notebook on Kubeflow

If you have not already done so, follow the Kubeflow getting [started guide](https://www.kubeflow.org/docs/started/) to deploy Kubeflow.

Then follow the Kubeflow [instructions](https://www.kubeflow.org/docs/components/jupyter/) to spawn a Jupyter notebook.

Once you've started Jupyter, start a shell and clone the repo.

```
git clone https://github.com/hamelsmu/MLapp.git git_mlapp
```

Then open the notebook fairing /label-prediction-fairing.ipynb

Then follow along in the notebook.