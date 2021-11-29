# -*- coding: utf-8 -*-
"""Proyecto_Final_Equipo05_1000.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1hW8IxRGswMX3-eT-9fPpyt42DQLiS7Pt

# NLP Final Project
## Jorge Alberto Padilla Gutiérrez A01625246
## Adrian Marcelo Suárez Ponce A01197108
## Marcos Leroy Salazar Skinner A01039743
## Jorge Antonio Ruiz Zavalza A01411162
## Guillermo Sáenz González A00823049

This guide follows closely with the [example](https://colab.research.google.com/github/huggingface/blog/blob/master/notebooks/trainer/01_text_classification.ipynb#scrollTo=bwl3I_VGAZXb) from HuggingFace for text classificaion on the GLUE dataset.

Install `multimodal-transformers`, `kaggle`  so we can get the dataset.
"""

!pip install multimodal-transformers
!pip install -q kaggle

"""## Setting up Kaggle
To get the dataset from kaggle we must upload our kaggle.json file containing our kaggle api token. See https://www.kaggle.com/docs/api for details.
"""

from google.colab import files
files.upload()

! mkdir ~/.kaggle
! cp kaggle.json ~/.kaggle/
! chmod 600 ~/.kaggle/kaggle.json
#! kaggle datasets list

"""## All other imports are here:"""

from dataclasses import dataclass, field
import json
import logging
import os
from typing import Optional

import seaborn as sns
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
from transformers import (
    AutoTokenizer,
    AutoConfig,
    Trainer,
    EvalPrediction,
    set_seed
)
from transformers.training_args import TrainingArguments

from multimodal_transformers.data import load_data_from_folder
from multimodal_transformers.model import TabularConfig
from multimodal_transformers.model import AutoModelWithTabular

logging.basicConfig(level=logging.INFO)
os.environ['COMET_MODE'] = 'DISABLED'

"""## Dataset

Our dataset is the [Womens Clothing E-Commerce Reviews](https://www.kaggle.com/nicapotato/womens-ecommerce-clothing-reviews) dataset from kaggle. It contains reviews written by customers about clothing items as well as whether they recommend the data or not. We download the dataset here.
"""

!kaggle datasets download -d snathjr/kindle-books-dataset

!ls

!unzip kindle-books-dataset.zip
!ls

"""#### Let us take a look at what the dataset looks like"""

data_df = pd.read_csv('Kindle_Book_Dataset.csv')
data_df.head(5)

# Find all the cells with nullish values
#missing_data = data_df.replace(['N/A', 'Unknown', 'Other'], np.nan)
#sns.heatmap(missing_data.isnull(), yticklabels=False, cbar=False, cmap='viridis')
data_df = data_df.dropna()

plt.figure(figsize=(15,7))
data_df['price'].nunique()
sns.displot(data_df['price'])

data_df['pages'].nunique()
sns.displot(data_df['pages'], log_scale=True)

sns.histplot(data=data_df['language'])

sns.displot(data=data_df['description'].apply(len), log_scale=True)

sns.displot(data_df['size'], log_scale=True)

sns.displot(data=data_df['customer_reviews'], log_scale=True)

print('Value Counts\n',data_df['stars'].value_counts())
sns.countplot(data=data_df, x='stars')

sns.heatmap(data_df.corr(), annot=True, fmt='.2')

"""We see that the data contains both text in the `Review Text` and `Title` column as well as tabular features in the `Division Name`, `Department Name`, and `Class Name` columns. """

data_df.describe(include=np.object)

data_df.describe()

"""Lets only keep the columns that are relevant"""

data_df = data_df.loc[:1250, ['title', 'description', 'price', 'pages', 'customer_reviews', 'stars']]

data_df.describe(include=np.object)

"""In this demonstration, we split our data into 8:1:1 training splits. We also save our splits to `train.csv`, `val.csv`, and `test.csv` as this is the format our dataloader requires.

"""

train_df, val_df, test_df = np.split(data_df.sample(frac=1), [int(.8*len(data_df)), int(.9 * len(data_df))])
print('Num examples train-val-test')
print(len(train_df), len(val_df), len(test_df))
train_df.to_csv('train.csv')
val_df.to_csv('val.csv')
test_df.to_csv('test.csv')

"""## We then define our Experiment Parameters
We use Data Classes to hold each of our arguments for the model, data, and training. 
"""

@dataclass
class ModelArguments:
  """
  Arguments pertaining to which model/config/tokenizer we are going to fine-tune from.
  """

  model_name_or_path: str = field(
      metadata={"help": "Path to pretrained model or model identifier from huggingface.co/models"}
  )
  config_name: Optional[str] = field(
      default=None, metadata={"help": "Pretrained config name or path if not the same as model_name"}
  )
  tokenizer_name: Optional[str] = field(
      default=None, metadata={"help": "Pretrained tokenizer name or path if not the same as model_name"}
  )
  cache_dir: Optional[str] = field(
      default=None, metadata={"help": "Where do you want to store the pretrained models downloaded from s3"}
  )


@dataclass
class MultimodalDataTrainingArguments:
  """
  Arguments pertaining to how we combine tabular features
  Using `HfArgumentParser` we can turn this class
  into argparse arguments to be able to specify them on
  the command line.
  """

  data_path: str = field(metadata={
                            'help': 'the path to the csv file containing the dataset'
                        })
  column_info_path: str = field(
      default=None,
      metadata={
          'help': 'the path to the json file detailing which columns are text, categorical, numerical, and the label'
  })

  column_info: dict = field(
      default=None,
      metadata={
          'help': 'a dict referencing the text, categorical, numerical, and label columns'
                  'its keys are text_cols, num_cols, cat_cols, and label_col'
  })

  categorical_encode_type: str = field(default='ohe',
                                        metadata={
                                            'help': 'sklearn encoder to use for categorical data',
                                            'choices': ['ohe', 'binary', 'label', 'none']
                                        })
  numerical_transformer_method: str = field(default='yeo_johnson',
                                            metadata={
                                                'help': 'sklearn numerical transformer to preprocess numerical data',
                                                'choices': ['yeo_johnson', 'box_cox', 'quantile_normal', 'none']
                                            })
  task: str = field(default="classification",
                    metadata={
                        "help": "The downstream training task",
                        "choices": ["classification", "regression"]
                    })

  mlp_division: int = field(default=4,
                            metadata={
                                'help': 'the ratio of the number of '
                                        'hidden dims in a current layer to the next MLP layer'
                            })
  combine_feat_method: str = field(default='individual_mlps_on_cat_and_numerical_feats_then_concat',
                                    metadata={
                                        'help': 'method to combine categorical and numerical features, '
                                                'see README for all the method'
                                    })
  mlp_dropout: float = field(default=0.1,
                              metadata={
                                'help': 'dropout ratio used for MLP layers'
                              })
  numerical_bn: bool = field(default=True,
                              metadata={
                                  'help': 'whether to use batchnorm on numerical features'
                              })
  use_simple_classifier: str = field(default=True,
                                      metadata={
                                          'help': 'whether to use single layer or MLP as final classifier'
                                      })
  mlp_act: str = field(default='relu',
                        metadata={
                            'help': 'the activation function to use for finetuning layers',
                            'choices': ['relu', 'prelu', 'sigmoid', 'tanh', 'linear']
                        })
  gating_beta: float = field(default=0.2,
                              metadata={
                                  'help': "the beta hyperparameters used for gating tabular data "
                                          "see https://www.aclweb.org/anthology/2020.acl-main.214.pdf"
                              })

  def __post_init__(self):
      assert self.column_info != self.column_info_path
      if self.column_info is None and self.column_info_path:
          with open(self.column_info_path, 'r') as f:
              self.column_info = json.load(f)

"""### Here are the data and training parameters we will use.
For model we can specify any supported HuggingFace model classes (see README for more details) as well as any AutoModel that are from the supported model classes. For the data specifications, we need to specify a dictionary that specifies which columns are the `text` columns, `numerical feature` columns, `categorical feature` column, and the `label` column. If we are doing classification, we can also specify what each of the labels means in the label column through the `label list`. We can also specifiy these columns using a path to a json file with the argument `column_info_path` to `MultimodalDataTrainingArguments`.
"""

# Columns: ['title', 'description', 'price', 'pages', 'customer_reviews', 'stars']
text_cols = ['title', 'description']
#cat_cols = ['Clothing ID', 'Division Name', 'Department Name', 'Class Name'] #No tenemos cols categoricas
numerical_cols = ['pages', 'price']

column_info_dict = {
    'text_cols': text_cols,
    'num_cols': numerical_cols,
    'cat_cols': [],
    'label_col': 'stars',
    'label_list': []
}


model_args = ModelArguments(
    model_name_or_path='bert-base-uncased'
)

data_args = MultimodalDataTrainingArguments(
    data_path='.',
    combine_feat_method='gating_on_cat_and_num_feats_then_sum',
    column_info=column_info_dict,
    task='regression'
)

training_args = TrainingArguments(
    output_dir="./logs/model_name",
    logging_dir="./logs/runs",
    overwrite_output_dir=True,
    do_train=True,
    do_eval=True,
    per_device_train_batch_size=4,
    num_train_epochs=1,
    evaluate_during_training=True,
    logging_steps=12,
    eval_steps=250,
    
)

set_seed(training_args.seed)

"""

```
# Tiene formato de código
```

## Now we can load our model and data. 
### We first instantiate our HuggingFace tokenizer
This is needed to prepare our custom torch dataset. See `torch_dataset.py` for details."""

tokenizer_path_or_name = model_args.tokenizer_name if model_args.tokenizer_name else model_args.model_name_or_path
print('Specified tokenizer: ', tokenizer_path_or_name)
tokenizer = AutoTokenizer.from_pretrained(
    tokenizer_path_or_name,
    cache_dir=model_args.cache_dir,
)

"""### Load dataset csvs to torch datasets
The function `load_data_from_folder` expects a path to a folder that contains `train.csv`, `test.csv`, and/or `val.csv` containing the respective split datasets. 
"""

# Get Datasets
train_dataset, val_dataset, test_dataset = load_data_from_folder(
    data_args.data_path,
    data_args.column_info['text_cols'],
    tokenizer,
    label_col=data_args.column_info['label_col'],
    label_list=data_args.column_info['label_list'],
    categorical_cols=data_args.column_info['cat_cols'],
    numerical_cols=data_args.column_info['num_cols'],
    sep_text_token_str=tokenizer.sep_token,
)

num_labels = len(np.unique(train_dataset.labels))
num_labels

config = AutoConfig.from_pretrained(
        model_args.config_name if model_args.config_name else model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
    )
tabular_config = TabularConfig(num_labels=num_labels,
                               numerical_feat_dim=train_dataset.numerical_feats.shape[1],
                               **vars(data_args))
config.tabular_config = tabular_config

model = AutoModelWithTabular.from_pretrained(
        model_args.config_name if model_args.config_name else model_args.model_name_or_path,
        config=config,
        cache_dir=model_args.cache_dir
    )

"""### We need to define a task-specific way of computing relevant metrics:"""

import numpy as np
from scipy.special import softmax
from sklearn.metrics import (
    # auc,
    # precision_recall_curve,
    # roc_auc_score,
    # f1_score,
    # confusion_matrix,
    # matthews_corrcoef,
    mean_absolute_error,
    mean_squared_error,
    r2_score,

)

def calc_classification_metrics(p: EvalPrediction):
  pred_labels = np.argmax(p.predictions, axis=1)
  pred_scores = softmax(p.predictions, axis=1)[:, 1]
  labels = p.label_ids

  return {
    'mean_absolute_error': mean_absolute_error(labels, pred_labels),
    'neg_mean_squared_error': mean_squared_error(labels, pred_labels),
    'r2': r2_score(labels, pred_labels),
  }

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=calc_classification_metrics,
)

"""## Launching the training is as simple is doing trainer.train() 🤗"""

#%%time
trainer.train()

"""### Check that our training was successful using TensorBoard"""

# Commented out IPython magic to ensure Python compatibility.
# Load the TensorBoard notebook extension
# %load_ext tensorboard

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir ./logs/runs --port=6006



"""## Interface



"""

pip install streamlit

pip install pyngrok==4.1.10

from google.colab import files
files.upload()

! mkdir ~/.kaggle

! cp kaggle.json ~/.kaggle/

! chmod 600 ~/.kaggle/kaggle.json

!kaggle datasets download -d snathjr/kindle-books-dataset

!ls

!unzip kindle-books-dataset.zip
!ls

import pandas as pd
import numpy as np

data_df = pd.read_csv('Kindle_Book_Dataset.csv')
data_df.describe(include=np.object)
data_df = data_df.loc[:, ['title', 'description', 'price', 'pages', 'customer_reviews', 'stars']]
data_df = data_df.dropna()
data_df

train_df, val_df, test_df = np.split(data_df.sample(frac=1), [int(.8*len(data_df)), int(.9 * len(data_df))])
train_df = train_df.sample(frac=0.3, replace=True)
val_df = val_df.sample(frac=0.3, replace=True)
test_df = test_df.sample(frac=0.3, replace=True)
print('Num examples train-val-test')
print(len(train_df), len(val_df), len(test_df))
train_df.to_csv('train.csv')
val_df.to_csv('val.csv')
test_df.to_csv('test.csv')

predictions = trainer.predict(test_dataset)

pred_df = pd.DataFrame(predictions[1])
pred_df.to_csv('pred.csv')

# Commented out IPython magic to ensure Python compatibility.
# %%writefile app.py
# import streamlit as st
# import pandas as pd
# import numpy as np
# from google.cloud import bigquery
# from google.oauth2 import service_account
# import pandas_gbq
# import os
# from sklearn.ensemble import RandomForestRegressor
# from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
# 
# data = pd.read_csv('test.csv')
# pred = pd.read_csv('pred.csv')
# 
# header = st.container()
# dataset = st.container()
# features = st.container()
# modelTraining = st.container()
# prediction = st.container()
# 
# with header:
# 	st.title("Welcome to our books dataset")
#  
# with dataset:
# 	st.header("Data")
# 	st.write(data.head(20))
#  
# 	st.subheader('Customer reviews')
# 	customer_rev = pd.DataFrame(data['customer_reviews'].value_counts()).head(50)
# 	st.bar_chart(customer_rev)
#  
# 	st.subheader('Pages')
# 	pages_g = pd.DataFrame(data['pages'].value_counts()).head(50)
# 	st.bar_chart(pages_g)
#  
# 	st.subheader('Price')
# 	price_g = pd.DataFrame(data['price'].value_counts()).head(50)
# 	st.bar_chart(price_g)
#  
# 	st.subheader('Stars')
# 	stars_g = pd.DataFrame(data['stars'].value_counts()).head(50)
# 	st.bar_chart(stars_g)
# 
# with features:
# 	st.header("Features")
#  
# 	st.markdown('* **Recomendations**: Here you can put any kind of information')
# 	st.markdown('* **Interviews**: Here you can put any kind of inofmration')
#  
# 
# # with modelTraining:
# # 	st.header("Training Model")
# # 	st.text('Here you can choose hyperparameters of the model and see how the performance changes')
#  
# # 	sel_col, disp_col = st.columns(2)
# # 	max_depth = sel_col.slider('What should be the max depth of the model?', min_value=10, max_value=100, value=0, step=1)
#  
# # 	n_estimators = sel_col.selectbox('How many book should there be?', options=[100,200,300,'No limit'])
# 	
# # 	sel_col.text('Here is a list of features')
# # 	sel_col.write(data.columns)
#  
# with prediction:
# 	st.header("Prediction with Model")
# 	st.text('Here you can use the trained model to evaluate the accuracy')
# 
# 	sel_col, disp_col = st.columns(2)
# 	input_number = sel_col.slider('Which book do you want to predict?(as a number in our set)', min_value=0, max_value=100, value=0, step=1)
# 	# input_feature = sel_col.text_input('Which feature should be used as the input feature?')
# 	st.text(pred.iloc[input_number,1])
#  
# 
#  
# 	
# 	
# 	
# 	
# 	# input_feature = sel_col.text_input('Which feature should be used as the input feature?')
# 
# #	if n_estimators == 'No limit':
# #		regr = RandomForestRegressor(max_depth=max_depth)
# #	else:
# #		regr = RandomForestRegressor(max_depth=max_depth, n_estimators=n_estimators)
# #
# 
# #	X = data[[input_feature]]    
# #	y = data[['customer_reviews']]
# 
# #	regr.fit(X, y) 
# #	prediction = regr.predict(y)
# 
# #	disp_col.subheader('Mean absolute error:') 
# #	disp_col.write(mean_absolute_error(y, prediction))
#

!ls

"""Se modifica el token por usuario"""

!ngrok authtoken 21ZhSLeNerV4lvIDihRlxvjcYEe_2vphQzEM6EWBvPf2q6o6o

from pyngrok import ngrok

!streamlit run app.py &>/dev/null&

!pgrep streamlit

public_url = ngrok.connect(port='8501')

public_url
