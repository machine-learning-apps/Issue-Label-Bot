import pandas as pd
from sklearn.model_selection import train_test_split
from ktext.preprocess import processor
import dill as dpickle
import numpy as np


output_dir = "/data/"


base_url = 'https://storage.googleapis.com/codenet/issue_labels/'
df = pd.concat([pd.read_csv(base_url+f'00000000000{i}.csv.gz') for i in range(10)])
df = df[df['num_concurrent_classes'] <= 1]
df.to_pickle(output_dir + 'labeled_issues_df.pkl')

traindf, testdf = train_test_split(df, test_size=.15)
traindf.to_pickle(output_dir + 'traindf.pkl')
testdf.to_pickle(output_dir + 'testdf.pkl')

train_body_raw = traindf.body.tolist()
train_title_raw = traindf.title.tolist()
body_pp = processor(hueristic_pct_padding=.8, keep_n=8000)
train_body_vecs = body_pp.fit_transform(train_body_raw)
title_pp = processor(hueristic_pct_padding=.8, keep_n=5000)

# process the title data
train_title_vecs = title_pp.fit_transform(train_title_raw)
test_body_raw = testdf.body.tolist()
test_title_raw = testdf.title.tolist()

test_body_vecs = body_pp.transform_parallel(test_body_raw)
test_title_vecs = title_pp.transform_parallel(test_title_raw)

# Save the preprocessor
with open('body_pp.dpkl', 'wb') as f:
    dpickle.dump(body_pp, f)

with open('title_pp.dpkl', 'wb') as f:
    dpickle.dump(title_pp, f)

# Save the processed data
np.save(output_dir + 'train_title_vecs.npy', train_title_vecs)
np.save(output_dir + 'train_body_vecs.npy', train_body_vecs)
np.save(output_dir + 'test_body_vecs.npy', test_body_vecs)
np.save(output_dir + 'test_title_vecs.npy', test_title_vecs)

train_labels = traindf[['c_bug', 'c_feature', 'c_question', 'c_other']].astype(int).values.argmax(axis=1)
test_labels = testdf[['c_bug', 'c_feature', 'c_question', 'c_other']].astype(int).values.argmax(axis=1)

np.save(output_dir + 'train_labels.npy', train_labels)
np.save(output_dir + 'test_labels.npy', test_labels)

assert train_body_vecs.shape[0] == train_title_vecs.shape[0] == train_labels.shape[0]
assert test_body_vecs.shape[0] == test_title_vecs.shape[0] == test_labels.shape[0]