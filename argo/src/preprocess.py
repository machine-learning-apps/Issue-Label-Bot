import pandas as pd
import dask.dataframe as df
from dask_ml.preprocessing import OneHotEncoder
import numpy as np
from keras.utils.np_utils import to_categorical
from dask.distributed import Client
import time
import json
import os

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

client = Client(os.getenv("DASK_SCHEDULER_ADDRESS"))

start_time = time.time()

output_dir = "/data/"

base_url = 'https://storage.googleapis.com/codenet/issue_labels/'
dd = df.from_pandas(pd.concat([pd.read_csv(base_url+f'00000000000{i}.csv.gz') for i in range(10)]), npartitions=1024)

def textacy_cleaner(text: str) -> str:
    """a
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
    if doc and len(doc) > 20000:
        return ["_start_", "", "_end_"]
    doc = text_to_word_sequence(textacy_cleaner(doc))
    if len(doc) > 1000:
        return ["_start_", "", "_end_"]
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

body_quant = int(bodies_parsed.apply(len).quantile(q=0.85).compute())
title_quant = int(titles_parsed.apply(len).quantile(q=0.85).compute())

print(f"Quantiles title-{title_quant} body-{body_quant} ")

def drop_long_docs(doc, max_len):
    if len(doc) > max_len:
        return doc[:max_len]
    return doc

bodies_parsed = bodies_parsed.apply(drop_long_docs, max_len=body_quant)
titles_parsed = titles_parsed.apply(drop_long_docs, max_len=title_quant)

def count_words(partition):
    c = Counter()
    def count(p):
        c.update(p)
        return c
    ct = Counter()
    ct.update(dict(partition.apply(count).iloc[0].most_common(n=8000)))
    return ct


now = time.time() - start_time
print(f"quantiles done {now}")


body_counts = bodies_parsed.map_partitions(count_words).compute()
now = time.time() - start_time
print(f"body counts computed {now}")
body_counts = sum(body_counts.tolist(), Counter())
now = time.time() - start_time
print(f"body-counts done {now}")
title_counts = titles_parsed.map_partitions(count_words).compute()
title_counts = sum(title_counts.tolist(), Counter())

now = time.time() - start_time
print(f"counting words body {now}")

words_to_keep_body = body_counts.most_common(n=8000)
body_vocab = defaultdict(lambda: 1)
body_vocab.update({x:i+2 for i, x in enumerate([x[0] for x in words_to_keep_body])})

now = time.time() - start_time
print(f"counting words title {now}")
words_to_keep_title = title_counts.most_common(n=4500)
titles_vocab = defaultdict(lambda: 1)
titles_vocab.update({x:i+2 for i, x in enumerate([x[0] for x in words_to_keep_title])})

now = time.time() - start_time
print(f"words counted {now}")

numer_bodies = bodies_parsed.apply(lambda x: [body_vocab[w] for w in x])
numer_titles = titles_parsed.apply(lambda x: [titles_vocab[w] for w in x])

def pad_partition(numerized_doc, max_len):
    if type(numerized_doc) != list:
        return
    return pad_sequences([numerized_doc], maxlen=max_len, truncating='post')[0]

processed_bodies = numer_bodies.apply(pad_partition, max_len=body_quant)
processed_titles = numer_titles.apply(pad_partition, max_len=title_quant)

now = time.time() - start_time
print(f"saving {now}")

processed_titles = np.stack(processed_titles.values.compute())
processed_bodies = np.stack(processed_bodies.values.compute())

now = time.time() - start_time
print(f"creating hdf5 {now}")


f = h5py.File('/data/dataset.hdf5', 'w')
f.create_dataset('/titles', data=processed_titles)
f.create_dataset('/bodies', data=processed_bodies)
f.create_dataset('/targets', data=targets)
f.close()

with open("/data/metadata.json", "w") as f:
    meta = {
        'body_vocab_size': len(body_vocab),
        'title_vocab_size': len(titles_vocab),
        'issue_body_doc_length': body_quant,
        'issue_title_doc_length': title_quant,
    }
    f.write(json.dumps(meta))


now = time.time() - start_time
print(f"saved {now}")