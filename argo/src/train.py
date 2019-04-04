import numpy as np
import dill as dpickle

import tensorflow as tf
from tensorflow.keras.utils import multi_gpu_model
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, GRU, Dense, Embedding, Conv1D, Bidirectional, BatchNormalization, Dot, Flatten, Concatenate
from tensorflow.keras.optimizers import Nadam
from tensorflow.keras.callbacks import CSVLogger, ModelCheckpoint




input_dir = "/data/"
out_dir = "/output/"

def load_pickle(fname):
    "load file pickled with dill."
    with open(fname, 'rb') as f:
        pp = dpickle.load(f)
    return pp

#load the text pre-processors
title_pp = load_pickle(input_dir + 'title_pp.dpkl')
body_pp = load_pickle(input_dir + 'body_pp.dpkl')

#load the training data and labels
train_body_vecs = np.load(input_dir + 'train_body_vecs.npy')
train_title_vecs = np.load(input_dir + 'train_title_vecs.npy')
train_labels = np.load(input_dir + 'train_labels.npy')

#load the test data and labels
test_body_vecs = np.load(input_dir + 'test_body_vecs.npy')
test_title_vecs = np.load(input_dir + 'test_title_vecs.npy')
test_labels = np.load(input_dir + 'test_labels.npy')


issue_body_doc_length = train_body_vecs.shape[1]
issue_title_doc_length = train_title_vecs.shape[1]

body_vocab_size = body_pp.n_tokens
title_vocab_size = title_pp.n_tokens

body_emb_size = 400
title_emb_size = 300

num_classes = len(set(train_labels))

body_input = Input(shape=(issue_body_doc_length,), name='Body-Input')
title_input = Input(shape=(issue_title_doc_length,), name='Title-Input')

b_i = Embedding(body_vocab_size, body_emb_size, name='Body-Embedding', mask_zero=False)(body_input)
b_t = Embedding(title_vocab_size, title_emb_size, name='Title-Embedding', mask_zero=False)(title_input)

b_i = BatchNormalization()(b_i)
b_i = Bidirectional(GRU(300, name='Body-Encoder'))(b_i)

b_t = BatchNormalization()(b_t)
b_t = GRU(300, name='Title-Encoder')(b_t)

b = Concatenate(name='Concat')([b_i, b_t])
#b = Dense(100, activation='relu', name='Dense1')(b_concat)
b = BatchNormalization()(b)
out = Dense(num_classes, activation='softmax')(b)

parallel_model = Model([body_input, title_input], out)
parallel_model.compile(optimizer=Nadam(lr=0.001), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

script_name_base = 'IssueLabeler'
csv_logger = CSVLogger(out_dir + '{:}.log'.format(script_name_base))
model_checkpoint = ModelCheckpoint(out_dir + '{:}.epoch{{epoch:02d}}-val{{val_loss:.5f}}.hdf5'.format(script_name_base),
                                   save_best_only=True)

batch_size = 6400
epochs = 10
history = parallel_model.fit(x=[train_body_vecs, train_title_vecs], 
                             y=np.expand_dims(train_labels, -1),
                             batch_size=batch_size,
                             epochs=epochs,
                             validation_split=0.10, 
                             callbacks=[csv_logger, model_checkpoint])
