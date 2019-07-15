# Deploying This Microservice: GitHub Issue Featurizer

This directory contains manifests for the backend of the microservice that returns embeddings given an issue label and body.  This backend is associated with associated with gh-issue-labeler.com/text.

This is currently running on a GKE cluster.


## issue-label-bot-dev

There is a dedicated instance running in

* **GCP project**: issue-label-bot-dev
* **cluster**: github-api-cluster
* **namespace**: issuefeat

Deploying it

1. Create the deployment

   ```
   kubectl apply -f deployments.yaml  
   ```

1. Create the secret

   ```
   gsutil cp gs://github-probots_secrets/issuefeat-secret.yaml /tmp
   kubectl -n issuefeat apply -f /tmp/issuefeat-secret.yaml
   ```

1. Create the ingress

   ```
   kubectl -n issuefeat apply -f ingress.yaml
   ```
