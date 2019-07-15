import numpy as np

# Because of error when using a virutal env
# https://markhneedham.com/blog/2018/05/04/python-runtime-error-osx-matplotlib-not-installed-as-framework-mac/
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from sklearn import svm, datasets
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, precision_recall_curve
from sklearn.utils.multiclass import unique_labels


def plot_confusion_matrix(y_true, y_pred, classes,
                          normalize=False,
                          title=None,
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if not title:
        if normalize:
            title = 'Normalized confusion matrix'
        else:
            title = 'Confusion matrix, without normalization'

    # Compute confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    # Only use the labels that appear in the data
    classes = classes[unique_labels(y_true, y_pred)]
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    fig, ax = plt.subplots()
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)
    # We want to show all ticks...
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           # ... and label them with the respective list entries
           xticklabels=classes, yticklabels=classes,
           title=title,
           ylabel='True label',
           xlabel='Predicted label')

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    return ax


class IssueLabeler:
    def __init__(self, 
                 body_text_preprocessor, 
                 title_text_preprocessor, 
                 model, 
                 class_names=['bug', 'feature_request', 'question']):
        """
        Parameters
        ----------
        body_text_preprocessor: ktext.preprocess.processor
            the text preprocessor trained on issue bodies
        title_text_preprocessor: ktext.preprocess.processor
            text preprocessor trained on issue titles
        model: tensorflow.keras.models
            a keras model that takes as input two tensors: vectorized 
            issue body and issue title.
        class_names: list
            class names as they correspond to the integer indices supplied to the model. 
        """
        self.body_pp = body_text_preprocessor
        self.title_pp = title_text_preprocessor
        self.model = model
        self.class_names = class_names
        
    
    def get_probabilities(self, body:str, title:str):
        """
        Get probabilities for the each class. 
        
        Parameters
        ----------
        body: str
           the issue body
        title: str
            the issue title
            
        Returns
        ------
        Dict[str:float]
        
        Example
        -------
        >>> issue_labeler = IssueLabeler(body_pp, title_pp, model)
        >>> issue_labeler.get_probabilities('hello world', 'hello world')
        {'bug': 0.08372017741203308,
         'feature': 0.6401631832122803,
         'question': 0.2761166989803314}
        """
        #transform raw text into array of ints
        vec_body = self.body_pp.transform([body])
        vec_title = self.title_pp.transform([title])
        
        # get predictions
        probs = self.model.predict(x=[vec_body, vec_title]).tolist()[0]
        
        return {k:v for k,v in zip(self.class_names, probs)}


def plot_precision_recall_vs_threshold(y, y_hat, class_names, precision_threshold):
    "plot precision recall curves focused on precision."
    # credit: https://github.com/ageron/handson-ml/blob/master/03_classification.ipynb
    assert len(class_names)-1 <= y_hat.shape[-1], 'number of class names must equal number of classes in the data'
    assert y.shape == y_hat.shape, 'shape of ground_truth and predictions must be the same.'
    
    for class_name in class_names:
        class_int = class_names.index(class_name)
        precisions, recalls, thresholds = precision_recall_curve(y[:, class_int], y_hat[:, class_int])
        
        # get the first index of the precision that meets the threshold
        precision_idx = np.argmax(precisions >= precision_threshold)
        # find the exact probability at that threshold
        prob_thresh = thresholds[precision_idx]
        # find the exact recall at that threshold
        recall_at_thresh = recalls[precision_idx]
        
        plt.figure(figsize=(8, 4))
        plt.plot(thresholds, precisions[:-1], "b--", label="Precision", linewidth=2)
        plt.plot(thresholds, recalls[:-1], "g-", label="Recall", linewidth=2)
        plt.axhline(y=precision_threshold, label=f'{precision_threshold:.2f}', linewidth=1)
        plt.xlabel("Threshold", fontsize=11)
        plt.legend(loc="lower left", fontsize=10)
        plt.title(f'Precision vs. Recall For Label: {class_name}')
        plt.ylim([0, 1])
        plt.xlim([0, 1])
        plt.show()
        print(f'Label "{class_name}" @ {precision_threshold:.2f} precision:')
        print(f'  Cutoff: {prob_thresh:.2f}')
        print(f'  Recall: {recall_at_thresh:.2f}')
        print('\n')