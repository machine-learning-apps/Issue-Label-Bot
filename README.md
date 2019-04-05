[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)

Code for Medium article: ["How to create machine learning products that automate tasks on GitHub for fun and profit"]()

# Issue-Label Bot

A [GitHub App](https://developer.github.com/apps/) powered by machine learning, written in python.  A detailed discussion behind the motivation for this app and an explanation of the components are located in the [blog article]() mentioned above.

### Links

 - GitHub App home page For [Issue-Label Bot](https://github.com/apps/issue-label-bot).
 - [Prediction Dashboard](http://mlbot.net:3000/) you can see examples of predictions for issues made.

### Deployment
You can deploy this app using [Heroku](https://devcenter.heroku.com/articles/container-registry-and-runtime) (easy) or a Kubernetees cluster (more advanced).  There are several environment variables that you must pass to the Docker container if you wish to run the app:

1. PRIVATE_KEY:  this is the private key you use to [authenticate as an app](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment) with the GitHub api.
2. DATABASE_URL: this is the URL that contains the login information for your POSTGRESQL database, usually in the form: `postgres://<username>:<password>@<url>:5432/<database_name>`
3. APP_ID: this is a unique identifier provided to you by GitHub when you [register your app](https://developer.github.com/apps/quickstart-guides/setting-up-your-development-environment).
4. FLASK_ENV: this is usually set to either `production` or `development`, you only want to use `deployment` for local testing.
5. PORT: this is the port your app will be serving on.  Note that if you are deploying to Heroku, Heroku will override this variable with their own value when building your app.
6. APP_URL: this is the url for the homepage of your app.  This allows you to switch domains etc. as necessary.

In Heroku, secrets can be passed in as [configuration variables](https://devcenter.heroku.com/articles/config-vars)
[This documentation](https://kubernetes.io/docs/concepts/configuration/secret/#creating-a-secret-manually) describes how you can set secrets in Kubernetees.

#### Notes

Deprecated Heroku site: [dead link](https://fathomless-forest-27162.herokuapp.com/)
