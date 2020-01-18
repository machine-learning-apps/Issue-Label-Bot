# Developer guide

1. You can deploy the front end using skaffold

   ```
   skaffold dev --cleanup=False
   ```

   * Your Kubernetes context should be set to using the `github-probots-dev` namespace
   * This will continually rebuild and upate your code
   * Skaffold's file sync feature is used to update the code in the image without rebuilding and
     redeploying
   * This makes redeploying very easy.

1. To send a GitHub webhook event you can either open up an issue or you can use `scripts/send_request.py`

   * The latter is useful because it avoids needing to open up a new GitHub issue

     * Right now the bot is only designed to respond to issues opened events.