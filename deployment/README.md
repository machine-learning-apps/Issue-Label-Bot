# Deploying MLApp

This directory contains manifests for the backend of the mlapp associated
with mlbot.net.

This is currently running on a GKE cluster.


## github-probots

There is a dedicated instance running in

* **GCP project**: github-probots
* **cluster**: kf-ci-ml
* **namespace**: mlapp

Deploying it

1. Create the deployment

   ```
   kubectl apply -f deployments.yaml  
   ```

1. Create the secret

   ```
   gsutil cp gs://github-probots_secrets/ml-app-inference-secret.yaml /tmp
   kubectl apply -f /tmp/ml-app-inference-secret.yaml
   ```

1. Create the ingress

   ```
   kubectl apply -f ingress.yaml
   ```