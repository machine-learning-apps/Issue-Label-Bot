import os
import yaml
from google.cloud import pubsub

project_id = os.environ['GCP_PROJECT_ID']
topic_name = 'event_queue'

def get_forwarded_repos(yaml_path='forwarded_repo.yaml'):
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['repos']

def create_topic():
    """
    Create a new pubsub topic.
    This function should only be called once while setup.
    """
    publisher = pubsub.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)
    publisher.create_topic(topic_path)

def publish_message(installation_id, repo_owner, repo_name, issue_num):
    """
    Publish a message to a pubsub topic.
    Args:
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
