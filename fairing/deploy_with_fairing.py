import argparse
import logging
import fairing
from fairing.builders.append import append
import fnmatch
import numpy as np
import os
import shutil
import tempfile

def deploy(registry, base_image):
  logging.getLogger().setLevel(logging.INFO)
  fairing.config.set_builder('append', registry=registry, base_image=base_image)

  # Add a common label.
  labels = {
    "app": "mlapp",
  }
  fairing.config.set_deployer('serving', serving_class="LabelPrediction",
                              labels=labels)

  # Get the list of all the python files
  this_dir = os.path.dirname(__file__)
  base_dir = os.path.abspath(os.path.join(this_dir, ".."))
  flask_dir = os.path.join(base_dir, "flask_app")
  input_files = []

  # Context gymnastics.
  # Create a directory with the desired layout for app.
  # We need to flatten things because Seldon expects the interface module
  # to be a top level module.
  #
  # TODO(https://github.com/SeldonIO/seldon-core/issues/465): Seldon
  # can't handle the module being nested; it needs to be top level module.

  context_dir = tempfile.mkdtemp()

  logging.info("Using context dir %s", context_dir)

  for dir_to_copy in [flask_dir, this_dir]:
    for root, dirs, files in os.walk(dir_to_copy, topdown=False):
      for name in files:
        if not fnmatch.fnmatch(name, "*.py"):
          continue
        shutil.copyfile(os.path.join(root, name),
                        os.path.join(context_dir, name))
        input_files.append(name)

  # Need to change to context_dir so that paths are added at the correct
  # location in the context .tar.gz
  os.chdir(context_dir)
  fairing.config.set_preprocessor('python', input_files=input_files)
  fairing.config.run()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--registry", default="", type=str,
    help=("The registry where your images should be pushed"))

  parser.add_argument(
    "--base_image", default="", type=str,
    help=("The base image to use"))

  args = parser.parse_args()
  deploy(args.registry, args.base_image)