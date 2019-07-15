# Code Intelligence: ML-Powered Developer Tools
Made with [Kubeflow](https://www.kubeflow.org/)

### **Motivation:**
One of the promises of machine learning is to automate mundane tasks and augment our capabilities, making us all more productive.  However, one domain that doesn’t get much attention that is ripe for more automation is the domain of software development itself.  This repository contains projects that are **live machine learning-powered devloper tools, usually in the form of GitHub apps, plugins or APIs.**  

We build these tools with the help of Kubeflow, in order to dog-food tools that Kubeflow developers themselves will benefit from, but also to surface real-world examples of end-to-end machine learning applications built with Kubeflow.

# Projects

### Deployed

1. [Issue-Label-Bot-v1](https://github.com/marketplace/issue-label-bot): A GitHub App that automatically labels issues as either a feature request, bug or question, using machine learning. 

2. [Issue-Embeddings](/Issue-Embeddings): A REST-API that returns 2400 dimensional embedding given an issue title and body.  This can be used for several downstream applications such as (1) label prediction, (2) duplicate detection (3) reviewer recommendation, etc.  You can also retrieve the embeddings for all issues in a repo in bulk at once.

### Under Construction :construction:

1. [Issue-Label-Bot-v2](/Issue-Label-Bot-v2): An improvement upon the [previous version](https://github.com/marketplace/issue-label-bot) of Issue-Label-Bot that predicts personalized issue labels, using the [Issue-Embeddings](/Issue-Embeddings) API.