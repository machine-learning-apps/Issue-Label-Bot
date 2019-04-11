import numpy as np
import dill as dpickle
import h5py
import json
from sklearn.model_selection import train_test_split

import tensorflow as tf
from tensorflow.keras.utils import multi_gpu_model
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, GRU, Dense, Embedding, Conv1D, Bidirectional, BatchNormalization, Dot, Flatten, Concatenate
from tensorflow.keras.optimizers import Nadam
from tensorflow.keras.callbacks import CSVLogger, ModelCheckpoint




input_dir = "/data/"
out_dir = "/output/"
dataset = h5py.File('/data/dataset.hdf5', 'r')
with open("/data/metadata.json", "r") as f:
    meta = json.loads(f.read())


train_bodies, test_bodies, train_titles, test_titles, train_targets, test_targets = train_test_split(
    np.array(dataset['bodies']),
    np.array(dataset['titles']),
    np.array(dataset['targets']),
    test_size=0.25
)

body_emb_size = 50
title_emb_size = 50

num_classes = 3

body_input = Input(shape=(meta['issue_body_doc_length'],), name='Body-Input')
title_input = Input(shape=(meta['issue_title_doc_length'],), name='Title-Input')

b_i = Embedding(meta['body_vocab_size']+1, body_emb_size, name='Body-Embedding', mask_zero=False)(body_input)
b_t = Embedding(meta['title_vocab_size']+1, title_emb_size, name='Title-Embedding', mask_zero=False)(title_input)

b_i = BatchNormalization()(b_i)
b_i = Bidirectional(GRU(100, name='Body-Encoder'))(b_i)

b_t = BatchNormalization()(b_t)
b_t = GRU(75, name='Title-Encoder')(b_t)

b = Concatenate(name='Concat')([b_i, b_t])
b = BatchNormalization()(b)
out = Dense(num_classes, activation='softmax')(b)

parallel_model = Model([body_input, title_input], out)
parallel_model.compile(optimizer=Nadam(lr=0.001), loss='categorical_crossentropy', metrics=['accuracy'])

script_name_base = 'IssueLabeler'
csv_logger = CSVLogger(out_dir + '{:}.log'.format(script_name_base))
model_checkpoint = ModelCheckpoint(out_dir + '{:}.epoch{{epoch:02d}}-val{{val_loss:.5f}}.hdf5'.format(script_name_base),
                                   save_best_only=True)

batch_size = 900
epochs = 4
history = parallel_model.fit(x=[train_bodies, train_titles], 
                             y=train_targets,
                             batch_size=batch_size,
                             epochs=epochs,
                             validation_split=0.10, 
                             callbacks=[csv_logger, model_checkpoint])
