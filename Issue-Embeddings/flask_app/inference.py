from mdparse.parser import transform_pre_rules, compose
from fastai.text.transform import defaults
from fastai.core import PathOrStr
from fastai.basic_train import load_learner
from torch import Tensor, cat
import pandas as pd
from tqdm.auto import tqdm

def pass_through(x):
    return x

class InferenceWrapper:
    def __init__(self, 
                 model_path:PathOrStr,
                 model_file_name:PathOrStr):

        self.learn = load_learner(path=model_path, file=model_file_name)
        self.learn.model.eval()  # turn off dropout, etc. only need to do this after loading model.
        self.encoder = self.learn.model[0]
    
    @staticmethod
    def parse(x: str) -> str:
        return compose(transform_pre_rules+defaults.text_pre_rules)(x)
    
    
    def numericalize(self, x:str) -> Tensor:
        return self.learn.data.one_item(self.parse(x))
    
    def get_raw_features(self, x:str) -> Tensor:
        """
        Get features from encoder of the language model.
        
        Returns Tensor of the shape (1, sequence-length, ndim)
        """
        seq_ints = self.numericalize(x)[0]
        self.encoder.reset() # so the hidden states reset between predictions
        
        return self.encoder.forward(seq_ints)[-1][-1]
        
    
    def get_pooled_features(self, x:str) -> Tensor:
        "Get concatenation of [mean, max, last] of last hidden state."
        raw = self.get_raw_features(x)
        # return [mean, max, last] with size of (1, self.learn.emb_sz * 3)
        return cat([raw.mean(dim=1), raw.max(dim=1)[0], raw[:,-1,:]], dim=-1)
    
    @classmethod
    def process_dict(cls, dfdict):
        """process the data from a dict, but allow failure."""
        title = dfdict['title']
        body = dfdict['body']
        try:
            text = 'xxxfldtitle '+ cls.parse(title) + ' xxxfldbody ' + cls.parse(body)
        except Exception as e:
            print(e)
            return {'text': 'xxxUnk'}
        return {'text': text}
    
    @classmethod
    def process_df(cls, dataframe:pd.DataFrame) -> pd.DataFrame:
        """Loop through a pandas DataFrame and create a single text field."""
        lst = []
        for d in tqdm(dataframe.to_dict(orient='rows')):
            lst.append(cls.process_dict(d))
        
        df = pd.DataFrame(lst)
        return df