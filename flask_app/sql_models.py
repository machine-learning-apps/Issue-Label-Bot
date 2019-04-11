import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Issues(db.Model):
    __tablename__ = "issues"
    issue_id = db.Column(db.Integer, primary_key=True)
    repo = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    issue_num = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=True)
    # the below statement allows you to call `Predictions.issue` to refer back to the issue
    predictions = db.relationship('Predictions', backref='issue', lazy=True)

    def add_prediction(self, comment_id, prediction, probability, logs, threshold, labeled, prediction_type='issue label'):
        p = Predictions(issue_id = self.issue_id,
                        comment_id=comment_id,
                        prediction=prediction,
                        probability=probability,
                        likes=None,
                        dislikes=None,
                        prediction_type=prediction_type,
                        logs=logs,
                        threshold=threshold,
                        labeled=labeled)
        db.session.add(p)
        db.session.commit()


class Predictions(db.Model):
    __tablename__ = "predictions"
    prediction_id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.issue_id"), nullable=False)
    comment_id = db.Column(db.BigInteger, nullable=False)
    prediction = db.Column(db.String, nullable=False)
    probability = db.Column(db.Float, nullable=False)
    likes = db.Column(db.Integer, nullable=True)
    dislikes = db.Column(db.Integer, nullable=True)
    prediction_type = db.Column(db.String, nullable=False)
    logs = db.Column(db.String, nullable=True)
    threshold = db.Column(db.Float, nullable=False)
    labeled = db.Column(db.Boolean, nullable=False)

    def update_feedback(self, likes, dislikes):
        p = Predictions.get(self.prediction_id)
        p.likes = likes
        p.dislikes = dislikes