import os
import yaml
from google.cloud import pubsub

def get_forwarded_repos(yaml_path='forwarded_repo.yaml'):
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['repos']

def check_topic_path_exists(project_id, topic_path):
    """
    Check if the topic path exists in the project.
    Args:
      project_id: project id on GCP
      topic_path: topic path in pubsub

    Return
    ------
    bool
        topic_path exists or not
    """
    publisher = pubsub.PublisherClient()
    project_path = publisher.project_path(project_id)
    for existing_topic_path in publisher.list_topics(project_path):
        if existing_topic_path.name == topic_path:
            return True
    return False

def create_topic_if_not_exists(project_id, topic_name):
    """
    Create a new pubsub topic if the topic name does not exist in the project.
    Args:
      project_id: project id on GCP
      topic_name: topic name used to create topic path
    """
    publisher = pubsub.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)
    if check_topic_path_exists(project_id, topic_path):
        return
    publisher.create_topic(topic_path)

def publish_message(project_id, topic_name, installation_id,
                    repo_owner, repo_name, issue_num):
    """
    Publish a message to a pubsub topic.
    Args:
      project_id: project id on GCP
      topic_name: topic name used to create topic path
      installation_id: repo installation id
      repo_owner: repo owner
      repo_name: repo name
      issue_num: issue index
    """
    publisher = pubsub.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)
    # all attributes being published to pubsub must be sent as text strings
    publisher.publish(topic_path,
                      b'New issue.',
                      installation_id=str(installation_id),
                      repo_owner=repo_owner,
                      repo_name=repo_name,
                      issue_num=str(issue_num))
