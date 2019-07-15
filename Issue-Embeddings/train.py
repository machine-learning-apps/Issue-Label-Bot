from math import inf
from fastai.text import load_data
from fastai.text.learner import language_model_learner
from fastai.text.models import AWD_LSTM, awd_lstm_lm_config
from fastai.callback import Callback
from fastai.callbacks import EarlyStoppingCallback, SaveModelCallback, ReduceLROnPlateauCallback, CSVLogger
import pandas as pd
from pathlib import Path
import wandb
import fire

def pass_through(x):
    return x

class wandbCallback(Callback):
    # https://docs.fast.ai/callback.html#Classes-for-callback-implementors
    def __init__(self, Learner):
        self.learn=Learner
        self.best_val_loss = inf
    
    def on_epoch_end(self, **kwargs):
        train, loss, epoch = kwargs['train'], kwargs['smooth_loss'], kwargs['epoch']
        val_loss, val_acc = kwargs['last_metrics']
        
        
        if train:
            wandb.log({'train_loss': loss, 'epoch':epoch})

            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                wandb.run.summary.update({'bestmodel_val_loss': val_loss, 'bestmodel_val_acc': val_acc})

        else:
            wandb.log({'val_loss': val_loss, 'val_accuracy':val_acc})
        
    def on_step_end(self, **kwargs):
        if kwargs['iteration'] % 100 == 0:
            wandb.log({'train_loss':kwargs['last_loss'], 'step':kwargs['iteration']})


class LangModel:
    def __init__(self, data_path: str='lang_model',
                 emb_sz: int=800, qrnn: bool=False, bidir:bool =False, 
                 n_layers: int=4, n_hid: int=2500, bs: int=104, bptt: int=67, 
                 lr: float=0.0013, wd: float=.012, one_cycle: bool=True,
                 cycle_len: int=1) -> None:
        """ Instantiate AWD_LSTM Language Model with hyper-parameters.
        
        data_path: str
            path where databunch is loaded from
        emb_sz: int
            size of word embeddings
        qrnn: bool
            whether or not to use qrnn (requires CudNN)
        bidir: bool
            if RNN should be bi-directional
        n_layers: int
            number of layers in lang model
        n_hid: int
            number of hidden units in model
        lr: float
            learning rate
        bptt: int
            back-propigation-through-time; max sequence length through which gradients will be accumulated.
        bs: int
            batch size
        
        The hyper-parameters are stored in a fastai dict called `fastai.text.models.awd_lstm_lm_config`:
           {'emb_sz': 400, 'n_hid': 1150, 'n_layers': 3, 'pad_token': 1, 'qrnn': False, 'bidir': False, 'output_p': 0.1,
            'hidden_p': 0.15, 'input_p': 0.25, 'embed_p': 0.02,'weight_p': 0.2, 'tie_weights': True, 'out_bias': True}
        """
        self.lr, self.wd, self.one_cycle, self.cycle_len = lr, wd, one_cycle, cycle_len
        awd_lstm_lm_config.update(dict(emb_sz=emb_sz, qrnn=qrnn, bidir=bidir, n_layers=n_layers, n_hid=n_hid))
        #log params
        wb_handle = wandb.init(config=awd_lstm_lm_config)
        wandb.config.update({'data_path': str(data_path),
                             'bs': bs,
                             'bptt': bptt,
                             'lr': lr})
        self.csv_name = 'history_' + wb_handle.name
        wandb.config.update({'csvlog_save_path': self.csv_name})

        # instantiate databunch
        self.data_lm = load_data(data_path, bs=bs, bptt=bptt)


        # instantiate language model
        self.learn = language_model_learner(data=self.data_lm,
                                            arch=AWD_LSTM,
                                            pretrained=False,
                                            model_dir=Path('models_' + wb_handle.name),
                                            config=awd_lstm_lm_config)
        self.full_model_path = str(self.learn.path/self.learn.model_dir)
        wandb.config.update({'model_save_path': self.full_model_path})

        # prepare callbacks
        escb = EarlyStoppingCallback(learn=self.learn, patience=2)
        smcb = SaveModelCallback(learn=self.learn, name='best_' + wb_handle.name)
        rpcb = ReduceLROnPlateauCallback(learn=self.learn, patience=1)
        csvcb = CSVLogger(learn=self.learn, filename=self.csv_name)
        wb = wandbCallback(self.learn)
        self.callbacks = [escb, smcb, rpcb, csvcb, wb]

        self.fit()

    def fit(self):
        "train the model."
        if self.one_cycle:
            self.learn.fit_one_cycle(cyc_len=self.cycle_len,
                                     max_lr=self.lr * 2,
                                     callbacks=self.callbacks)
        else:
            self.learn.fit(epochs=1, lr=self.lr, wd=self.wd, callbacks=self.callbacks)

        wandb.save(self.full_model_path)
        wandb.save(str(self.learn.path/self.csv_name) + '.csv')
        

if __name__== '__main__':
    fire.Fire(LangModel)