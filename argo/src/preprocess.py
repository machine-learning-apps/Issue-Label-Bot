import pandas as pd
import dask.dataframe as df
from dask_ml.preprocessing import OneHotEncoder
import numpy as np
from keras.utils.np_utils import to_categorical
import time

from sklearn.model_selection import train_test_split
from typing import Callable, List
from keras.preprocessing.text import text_to_word_sequence
from keras.preprocessing.sequence import pad_sequences
from dask import array as da
from textacy.preprocess import preprocess_text
import dask.multiprocessing
from pathos.multiprocessing import cpu_count
from collections import Counter
from collections import defaultdict
import h5py


start_time = time.time()

dask.config.set(scheduler='processes')

output_dir = "/data/"

base_url = 'https://storage.googleapis.com/codenet/issue_labels/'
dd = df.from_pandas(pd.concat([pd.read_csv(base_url+f'00000000000{i}.csv.gz') for i in range(10)]), npartitions=128)

print(dd.head())

def textacy_cleaner(text: str) -> str:
    """
    Defines the default function for cleaning text.

    This function operates over a list.
    """
    return preprocess_text(text,
                           fix_unicode=True,
                           lowercase=True,
                           transliterate=True,
                           no_urls=True,
                           no_emails=True,
                           no_phone_numbers=True,
                           no_numbers=True,
                           no_currency_symbols=True,
                           no_punct=True,
                           no_contractions=False,
                           no_accents=True)


def process_document(doc: str) -> List[str]:
    doc = text_to_word_sequence(textacy_cleaner(doc))
    return ["_start_"] + doc + ["_end_"]


test_data = 'hello world 314-903-3072, hamel.husain@gmail.com wee woo'
assert process_document(test_data) == ['_start_', 'hello', 'world', 'phone', 'email', 'wee', 'woo', '_end_']


bodies_parsed = dd["body"].apply(process_document)
titles_parsed = dd["title"].apply(process_document)

now = time.time() - start_time
print(f"tokenized {now}")

def to_one_hot(df):
    return to_categorical(df.values, num_classes=3)

targets = dd["class_int"].to_frame().map_partitions(to_one_hot)

body_quant = int(bodies_parsed.apply(len).quantile(q=0.75).compute())
title_quant = int(titles_parsed.apply(len).quantile(q=0.75).compute())

def count_words(partition):
    c = Counter()
    def count(p):
        c.update(p)
        return c
    return partition.apply(count).iloc[0]

body_counts = bodies_parsed.map_partitions(count_words).compute()
body_counts = sum(body_counts.tolist(), Counter())

title_counts = titles_parsed.map_partitions(count_words).compute()
title_counts = sum(title_counts.tolist(), Counter())


words_to_keep_body = body_counts.most_common(n=8000)
body_vocab = defaultdict(lambda: 1)
body_vocab.update({x:i+2 for i, x in enumerate([x[0] for x in words_to_keep_body])})

words_to_keep_title = title_counts.most_common(n=4500)
titles_vocab = defaultdict(lambda: 1)
titles_vocab.update({x:i+2 for i, x in enumerate([x[0] for x in words_to_keep_title])})

numer_bodies = bodies_parsed.apply(lambda x: [body_vocab[w] for w in x])
numer_titles = titles_parsed.apply(lambda x: [titles_vocab[w] for w in x])

def pad_partition(numerized_doc):
    if type(numerized_doc) != list:
        return
    return pad_sequences([numerized_doc], maxlen=body_quant, truncating='post')[0]

processed_bodies = numer_bodies.apply(pad_partition)
processed_titles = numer_titles.apply(pad_partition)

num_titles = processed_titles.count().compute()
num_bodies = processed_bodies.count().compute()

now = time.time() - start_time
print(f"saving {now}")

processed_titles = da.stack(processed_titles.values.compute())
processed_bodies = da.stack(processed_bodies.values.compute())

f = h5py.File('/data/output.hdf5', 'w')
f.create_dataset('/titles', data=processed_titles.compute())
f.create_dataset('/bodies', data=processed_bodies.compute())
f.create_dataset('/targets', data=targets.compute())
f.close()

now = time.time() - start_time
print(f"saved {now}")