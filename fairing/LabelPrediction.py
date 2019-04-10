# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Use Append builder and deploy the model.

The file needs to be named the same as the class containing the predict method.
This is how Seldon works.
https://docs.seldon.io/projects/seldon-core/en/latest/python/python_wrapping.html

This is the Seldon interface class.
"""

import app
import logging
import tensorflow as tf

class LabelPrediction(object):
  def __init__(self):
    """"""
    self.graph = None
    self.issue_labeler = None

  def predict(self, X, feature_names):
    """Predict using the model for given ndarray."""

    if self.issue_labeler is None:
      # Load the model.
      logging.info("Creating the issue labeler and initializing TF graph.")
      self.graph = tf.get_default_graph()
      self.issue_labeler = app.init_issue_labeler()

    probabilities = self.issue_labeler.get_probabilities(body=X[1],
                                                    title=X[0])

    logging.info("Probability keys: %s", probabilities.keys())

    p = [0] * 3
    for i, k in enumerate(["bug", "feature_request", "question"]):
      if not k in probabilities:
        continue
      p[i] = probabilities[k]

    return [p]
