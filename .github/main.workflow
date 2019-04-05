workflow "New workflow" {
  resolves = ["One Click Docker"]
  on = "push"
}

action "One Click Docker" {
  uses = "pangzineng/Github-Action-One-Click-Docker@v1.1.0"
  secrets = ["DOCKER_USERNAME", "DOCKER_PASSWORD"]
  env = {
    DOCKER_IMAGE_NAME = "hamelsmu/mlapp"
    BRANCH_FILTER = "docker-build"
  }
}
