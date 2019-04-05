workflow "New workflow" {
  resolves = ["One Click Docker"]
  on = "push"
}

action "One Click Docker" {
  uses = "pangzineng/Github-Action-One-Click-Docker@v1.1.0"
  args = "-f deployment/Dockerfile ."
  secrets = ["DOCKER_USERNAME", "DOCKER_PASSWORD"]
  env = {
    DOCKER_IMAGE_NAME = "mlapp"
    DOCKER_NAMESPACE = "hamelsmu"
  }
}
