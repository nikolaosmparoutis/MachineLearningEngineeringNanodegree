# %%
"""
# Detecting Payment Card Fraud

In this section, we'll look at a credit card fraud detection dataset, and build a binary classification model that can identify transactions as either fraudulent or valid, based on provided, *historical* data. In a [2016 study](https://nilsonreport.com/upload/content_promo/The_Nilson_Report_10-17-2016.pdf), it was estimated that credit card fraud was responsible for over 20 billion dollars in loss, worldwide. Accurately detecting cases of fraud is an ongoing area of research.

<img src=notebook_ims/fraud_detection.png width=50% />

### Labeled Data

The payment fraud data set (Dal Pozzolo et al. 2015) was downloaded from [Kaggle](https://www.kaggle.com/mlg-ulb/creditcardfraud/data). This has features and labels for thousands of credit card transactions, each of which is labeled as fraudulent or valid. In this notebook, we'd like to train a model based on the features of these transactions so that we can predict risky or fraudulent transactions in the future.

### Binary Classification

Since we have true labels to aim for, we'll take a **supervised learning** approach and train a binary classifier to sort data into one of our two transaction classes: fraudulent or valid.  We'll train a model on training data and see how well it generalizes on some test data.

The notebook will be broken down into a few steps:
* Loading and exploring the data
* Splitting the data into train/test sets
* Defining and training a LinearLearner, binary classifier
* Making improvements on the model
* Evaluating and comparing model test performance

### Making Improvements

A lot of this notebook will focus on making improvements, as discussed in [this SageMaker blog post](https://aws.amazon.com/blogs/machine-learning/train-faster-more-flexible-models-with-amazon-sagemaker-linear-learner/). Specifically, we'll address techniques for:

1. **Tuning a model's hyperparameters** and aiming for a specific metric, such as high recall or precision.
2. **Managing class imbalance**, which is when we have many more training examples in one class than another (in this case, many more valid transactions than fraudulent).

---
"""

# %%
"""
First, import the usual resources.
"""

# %%
import io
import os
import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd 

import boto3
import sagemaker
from sagemaker import get_execution_role

%matplotlib inline

# %%
"""
I'm storing my **SageMaker variables** in the next cell:
* sagemaker_session: The SageMaker session we'll use for training models.
* bucket: The name of the default S3 bucket that we'll use for data storage.
* role: The IAM role that defines our data and model permissions.
"""

# %%
# sagemaker session, role
sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()

# S3 bucket name
bucket = sagemaker_session.default_bucket()


# %%
"""
## Loading and Exploring the Data

Next, I am loading the data and unzipping the data in the file `creditcardfraud.zip`. This directory will hold one csv file of all the transaction data, `creditcard.csv`.

As in previous notebooks, it's important to look at the distribution of data since this will inform how we develop a fraud detection model. We'll want to know: How many data points we have to work with, the number and type of features, and finally, the distribution of data over the classes (valid or fraudulent).
"""

# %%
# only have to run once
# !wget https://s3.amazonaws.com/video.udacity-data.com/topher/2019/January/5c534768_creditcardfraud/creditcardfraud.zip
# !unzip creditcardfraud


# %%
# read in the csv file
local_data = 'creditcard.csv'

# print out some data
transaction_df = pd.read_csv(local_data)
print('Data shape (rows, cols): ', transaction_df.shape)
print()
transaction_df.head()

# %%
"""
### EXERCISE: Calculate the percentage of fraudulent data

Take a look at the distribution of this transaction data over the classes, valid and fraudulent. 

Complete the function `fraudulent_percentage`, below. Count up the number of data points in each class and calculate the *percentage* of the data points that are fraudulent.
"""

# %%
# Calculate the fraction of data points that are fraudulent
def fraudulent_percentage(transaction_df):
    '''Calculate the fraction of all data points that have a 'Class' label of 1; fraudulent.
       :param transaction_df: Dataframe of all transaction data points; has a column 'Class'
       :return: A fractional percentage of fraudulent data points/all points
    '''
    counts_per_class = transaction_df['Class'].value_counts()
    valid = counts_per_class[0]
    fraudulent = counts_per_class[1]
    return (fraudulent/transaction_df.shape[0])

# %%
"""
Test out your code by calling your function and printing the result.
"""

# %%
# call the function to calculate the fraud percentage
fraud_percentage = fraudulent_percentage(transaction_df)

print('Fraudulent percentage = ', fraud_percentage)
print('Total # of fraudulent pts: ', fraud_percentage*transaction_df.shape[0])
print('Out of (total) pts: ', transaction_df.shape[0])
print(transaction_df.head)

# %%
"""
### EXERCISE: Split into train/test datasets

In this example, we'll want to evaluate the performance of a fraud classifier; training it on some training data and testing it on *test data* that it did not see during the training process. So, we'll need to split the data into separate training and test sets.

Complete the `train_test_split` function, below. This function should:
* Shuffle the transaction data, randomly
* Split it into two sets according to the parameter `train_frac`
* Get train/test features and labels
* Return the tuples: (train_features, train_labels), (test_features, test_labels)
"""

# %%
# split into train/test
def train_test_split(transaction_df, train_frac= 0.7, seed=1):
    '''Shuffle the data and randomly split into train and test sets;
       separate the class labels (the column in transaction_df) from the features.
       :param df: Dataframe of all credit card transaction data
       :param train_frac: The decimal fraction of data that should be training data
       :param seed: Random seed for shuffling and reproducibility, default = 1
       :return: Two tuples (in order): (train_features, train_labels), (test_features, test_labels)
       '''
    
    # shuffle and split the data

    transaction_numpy = transaction_df.to_numpy() # suuperclass of as_matrix as it creates N dimensionall vs 2 D of as_matrix
    np.random.seed(seed)
    np.random.shuffle(transaction_numpy)
    length_train = int(train_frac * transaction_numpy.shape[0])
    length_test = int((1-train_frac) * transaction_numpy.shape[0])
    
    print("ratios", length_train/transaction_numpy.shape[0], length_test/transaction_numpy.shape[0] )
    print("ratios train/test", length_train/length_test)
    
    train_features =  transaction_numpy[:length_train,:-2]
    train_labels = transaction_numpy[:length_train,-1]
    
    test_features = transaction_numpy[length_train:,:-2]
    test_labels = transaction_numpy[length_train:,-1]
    
    return (train_features, train_labels), (test_features, test_labels)


# %%
"""
### Test Cell

In the cells below, I'm creating the train/test data and checking to see that result makes sense. The tests below test that the above function splits the data into the expected number of points and that the labels are indeed, class labels (0, 1).
"""

# %%
# get train/test data
(train_features, train_labels), (test_features, test_labels) = train_test_split(transaction_df, train_frac=0.7)

# %%
# manual test !!!

# for a split of 0.7:0.3 there should be ~2.33x as many training as test pts
print('Training data pts: ', len(train_features))
print('Test data pts: ', len(test_features))
print()

# take a look at first item and see that it aligns with first row of data
print('First item: \n', train_features[0])
print('Label: ', train_labels[0])
print()

# test split
assert len(train_features) > 2.333*len(test_features), \
        'Unexpected number of train/test points for a train_frac=0.7'
# test labels
assert np.all(train_labels)== 0 or np.all(train_labels)== 1, \
        'Train labels should be 0s or 1s.'
assert np.all(test_labels)== 0 or np.all(test_labels)== 1, \
        'Test labels should be 0s or 1s.'
print('Tests passed!')

# %%
"""
---
# Modeling

Now that you've uploaded your training data, it's time to define and train a model!

In this notebook, you'll define and train the SageMaker, built-in algorithm, [LinearLearner](https://sagemaker.readthedocs.io/en/stable/linear_learner.html). 

A LinearLearner has two main applications:
1. For regression tasks in which a linear line is fit to some data points, and you want to produce a predicted output value given some data point (example: predicting house prices given square area).
2. For binary classification, in which a line is separating two classes of data and effectively outputs labels; either 1 for data that falls above the line or 0 for points that fall on or below the line.

<img src='notebook_ims/linear_separator.png' width=50% />

In this case, we'll be using it for case 2, and we'll train it to separate data into our two classes: valid or fraudulent. 
"""

# %%
"""
### EXERCISE: Create a LinearLearner Estimator

You've had some practice instantiating built-in models in SageMaker. All estimators require some constructor arguments to be passed in. See if you can complete this task, instantiating a LinearLearner estimator, using only the [LinearLearner documentation](https://sagemaker.readthedocs.io/en/stable/linear_learner.html) as a resource. This takes in a lot of arguments, but not all are required. My suggestion is to start with a simple model, utilizing default values where applicable. Later, we will discuss some specific hyperparameters and their use cases.

#### Instance Types

It is suggested that you use instances that are available in the free tier of usage: `'ml.c4.xlarge'` for training and `'ml.t2.medium'` for deployment.
"""

# %%
stad_dev_train = np.std(train_features) # firstly  flattened the numpy array by default
print("stad_dev", stad_dev_train)

# %%
# import LinearLearner
from sagemaker import LinearLearner

# specify an output path
prefix = 'creditcard'
output_path = 's3://{}/{}'.format(bucket, prefix)

# instantiate LinearLearner
linear = LinearLearner(role=role,
                     instance_count=1,
                     instance_type='ml.c4.xlarge',
                     predictor_type='binary_classifier',
                     binary_classifier_model_selection_criteria='accuracy',
                     positive_example_weight_mult='balanced',
                     epochs=20,
                     init_method='normal', # weight initialization 
                     init_sigma=stad_dev_train,
                     optimizer='sgd',
                     loss='logistic',
                     learning_rate='0.01',
                     normalize_data=True,
                     normalize_label=True,
                     unbias_data=True,
                     unbias_label=True,
                     early_stopping_patience=15,
                     max_run =60 * 60 * 2,  # max timeout of trainning in seconds - 2 hours
                     output_path= output_path,
                     sagemaker_session=sagemaker_session
                     )


# %%
"""
### EXERCISE: Convert data into a RecordSet format

Next, prepare the data for a built-in model by **converting the train features and labels into numpy array's of float values**. Then you can use the [record_set function](https://sagemaker.readthedocs.io/en/stable/linear_learner.html#sagemaker.LinearLearner.record_set) to format the data as a RecordSet and prepare it for training! Recordsets atr 
"""

# %%
# create RecordSet of training data
x_recordset_train = train_features.astype('float32')
y_recordset_labels = train_labels.astype('float32')
formatted_train_data = linear.record_set(x_recordset_train,y_recordset_labels , channel='train', encrypt=False)

# %%
"""
### EXERCISE: Train the Estimator

After instantiating your estimator, train it with a call to `.fit()`, passing in the formatted training data.
"""

# %%
"""
### EXERCISE: Deploy the trained model

Deploy your model to create a predictor. We'll use this to make predictions on our test data and evaluate the model.
"""

# %%
%%time 
# train the estimator on formatted training data
linear.fit(formatted_train_data, wait=True, logs=True, job_name='fraud-detection-6-5')

# %%
%%time 
# deploy and create a predictor
linear_predictor = linear.deploy(initial_instance_count=1, 
                                 instance_type='ml.t2.medium', 
                                 endpoint_name='fraud-detection',
                                 wait=True,
                                 model_name='fraud-detection-06-05-2012')

# %%
"""
---
# Evaluating Your Model

Once your model is deployed, you can see how it performs when applied to the test data.

According to the deployed [predictor documentation](https://sagemaker.readthedocs.io/en/stable/linear_learner.html#sagemaker.LinearLearnerPredictor), this predictor expects an `ndarray` of input features and returns a list of Records.
> "The prediction is stored in the "predicted_label" key of the `Record.label` field."

Let's first test our model on just one test point, to see the resulting list.
"""

# %%
# test one prediction
test_x_np = test_features.astype('float32')
# for i in range(1,10):
result = linear_predictor.predict(test_x_np[0])
print(result)

# %%
"""
### Helper function for evaluation


The provided function below, takes in a deployed predictor, some test features and labels, and returns a dictionary of metrics; calculating false negatives and positives as well as recall, precision, and accuracy.
"""

# %%
# code to evaluate the endpoint on test data
# returns a variety of model metrics
def evaluate(predictor, test_features, test_labels, verbose=True):
    """
    Evaluate a model on a test set given the prediction endpoint.  
    Return binary classification metrics.
    :param predictor: A prediction endpoint
    :param test_features: Test features
    :param test_labels: Class labels for test data
    :param verbose: If True, prints a table of all performance metrics
    :return: A dictionary of performance metrics.
    """
    
    # We have a lot of test data, so we'll split it into batches of 100
    # split the test data set into batches and evaluate using prediction endpoint    
    prediction_batches = [predictor.predict(batch) for batch in np.array_split(test_features, 100)]
    
    # LinearLearner produces a `predicted_label` for each data point in a batch
    # get the 'predicted_label' for every point in a batch
    test_preds = np.concatenate([np.array([x.label['predicted_label'].float32_tensor.values[0] for x in batch]) 
                                 for batch in prediction_batches])
    
    # calculate true positives, false positives, true negatives, false negatives
    tp = np.logical_and(test_labels, test_preds).sum()
    fp = np.logical_and(1-test_labels, test_preds).sum()
    tn = np.logical_and(1-test_labels, 1-test_preds).sum()
    fn = np.logical_and(test_labels, 1-test_preds).sum()
    
    # calculate binary classification metrics
    recall = tp / (tp + fn)
    precision = tp / (tp + fp)
    accuracy = (tp + tn) / (tp + fp + tn + fn)
    
    # printing a table of metrics
    if verbose:
        print(pd.crosstab(test_labels, test_preds, rownames=['actual (row)'], colnames=['prediction (col)']))
        print("\n{:<11} {:.3f}".format('Recall:', recall))
        print("{:<11} {:.3f}".format('Precision:', precision))
        print("{:<11} {:.3f}".format('Accuracy:', accuracy))
        print()
        
    return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn, 
            'Precision': precision, 'Recall': recall, 'Accuracy': accuracy}


# %%
"""
### Test Results

The cell below runs the `evaluate` function. 

The code assumes that you have a defined `predictor` and `test_features` and `test_labels` from previously-run cells.
"""

# %%
print('Metrics for simple, LinearLearner.\n')

# get metrics for linear predictor
metrics = evaluate(linear_predictor, 
                   test_features.astype('float32'), 
                   test_labels, 
                   verbose=True) # verbose means we'll print out the metrics


# %%
"""
## Delete the Endpoint

I've added a convenience function to delete prediction endpoints after we're done with them. And if you're done evaluating the model, you should delete your model endpoint!
"""

# %%
# Deletes a precictor.endpoint
# def delete_endpoint(predictor):
#         try:
#             boto3.client('sagemaker').delete_endpoint(EndpointName=predictor.endpoint)
#             print('Deleted {}'.format(predictor.endpoint))
#         except:
#             print('Already deleted: {}'.format(predictor.endpoint))

# %%
# delete the predictor endpoint 
# delete_endpoint(linear_predictor)

# %%
"""
---

# Model Improvements

The default LinearLearner got a high accuracy, but still classified fraudulent and valid data points incorrectly. Specifically classifying more than 30 points as false negatives (incorrectly labeled, fraudulent transactions), and a little over 30 points as false positives (incorrectly labeled, valid transactions). Let's think about what, during training, could cause this behavior and what we could improve.

**1. Model optimization**
* If we imagine that we are designing this model for use in a bank application, we know that users do *not* want any valid transactions to be categorized as fraudulent. That is, we want to have as few **false positives** (0s classified as 1s) as possible. 
* On the other hand, if our bank manager asks for an application that will catch almost *all* cases of fraud, even if it means a higher number of false positives, then we'd want as few **false negatives** as possible.
* To train according to specific product demands and goals, we do not want to optimize for accuracy only. Instead, we want to optimize for a metric that can help us decrease the number of false positives or negatives. 

<img src='notebook_ims/precision_recall.png' width=40% />
     
In this notebook, we'll look at different cases for tuning a model and make an optimization decision, accordingly.

**2. Imbalanced training data**
* At the start of this notebook, we saw that only about 0.17% of the training data was labeled as fraudulent. So, even if a model labels **all** of our data as valid, it will still have a high accuracy. 
* This may result in some overfitting towards valid data, which accounts for some **false negatives**; cases in which fraudulent data (1) is incorrectly characterized as valid (0).

So, let's address these issues in order; first, tuning our model and optimizing for a specific metric during training, and second, accounting for class imbalance in the training set. 

"""

# %%
"""
## Improvement: Model Tuning

Optimizing according to a specific metric is called **model tuning**, and SageMaker provides a number of ways to automatically tune a model.


### Create a LinearLearner and tune for higher precision 

**Scenario:**
**A bank has asked you to build a model that detects cases of fraud with an accuracy of about 85%.** 

In this case, we want to build a model that has as many true positives and as few false negatives, as possible. This corresponds to a model with a high **recall**: true positives / (true positives + false negatives). 

To aim for a specific metric, LinearLearner offers the hyperparameter `binary_classifier_model_selection_criteria`, which is the model evaluation criteria for the training dataset. A reference to this parameter is in [LinearLearner's documentation](https://sagemaker.readthedocs.io/en/stable/linear_learner.html#sagemaker.LinearLearner). We'll also have to further specify the exact value we want to aim for; read more about the details of the parameters, [here](https://docs.aws.amazon.com/sagemaker/latest/dg/ll_hyperparameters.html).

**I will assume that performance on a training set will be within about 5% of the performance on a test set. So, for a recall of about 85%, I'll aim for a bit higher, 90%. We assume higher in trainning to get the lower of a realistic data, the testing.** 
"""

# %%
# instantiate a LinearLearner
# tune the model for a higher recall
linear_recall = LinearLearner(role=role,
                              train_instance_count=1, 
                              train_instance_type='ml.c4.xlarge',
                              predictor_type='binary_classifier',
                              output_path=output_path,
                              sagemaker_session=sagemaker_session,
                              epochs=15,
                              binary_classifier_model_selection_criteria='precision_at_target_recall', # target recall
                              target_recall=0.9) # 90% recall


# %%
"""
### Train the tuned estimator

Fit the new, tuned estimator on the formatted training data.
"""

# %%
%%time 
# train the estimator on formatted training data
linear_recall.fit(formatted_train_data)

# %%
"""
### Deploy and evaluate the tuned estimator

Deploy the tuned predictor and evaluate it.

We hypothesized that a tuned model, optimized for a higher recall, would have fewer false negatives (fraudulent transactions incorrectly labeled as valid); did the number of false negatives get reduced after tuning the model?
"""

# %%
%%time 
# deploy and create a predictor
recall_predictor = linear_recall.deploy(initial_instance_count=1, instance_type='ml.t2.medium',model_name='fraud-detection-optimus-06-05-2012')

# %%
print('Metrics for tuned (recall), LinearLearner.\n')

# get metrics for tuned predictor
metrics = evaluate(recall_predictor, 
                   test_features.astype('float32'), 
                   test_labels, 
                   verbose=True)

# %%
"""
## Delete the endpoint 

As always, when you're done evaluating a model, you should delete the endpoint. Below, I'm using the `delete_endpoint` helper function I defined earlier.
"""

# %%
# delete the predictor endpoint 
# delete_endpoint(recall_predictor)

# %%
"""
---
## Improvement: Managing Class Imbalance

We have a model that is tuned to get a higher recall, which aims to reduce the number of false negatives. Earlier, we discussed how class imbalance may actually bias our model towards predicting that all transactions are valid, resulting in higher false negatives and true negatives. It stands to reason that this model could be further improved if we account for this imbalance.

To account for class imbalance during training of a binary classifier, LinearLearner offers the hyperparameter, `positive_example_weight_mult`, which is **the weight assigned to positive (1, fraudulent)** examples when training a binary classifier. The weight of negative examples (0, valid) is fixed at 1. 

### EXERCISE: Create a LinearLearner with a `positive_example_weight_mult` parameter

In **addition** to tuning a model for higher recall (you may use `linear_recall` as a starting point), you should *add* a parameter that helps account for class imbalance. From the [hyperparameter documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/ll_hyperparameters.html) on `positive_example_weight_mult`, it reads:
> "If you want the algorithm to choose a weight so that errors in classifying negative vs. positive examples have equal impact on training loss, specify `balanced`."

You could also put in a specific float value, in which case you'd want to weight positive examples more heavily than negative examples, since there are fewer of them.
"""

# %%
# instantiate a LinearLearner

# include params for tuning for higher recall
# *and* account for class imbalance in training data
linear_balanced = LinearLearner(role,1, 'ml.c4.xlarge','binary_classifier',
                                output_path=output_path,
                                sagemaker_session=sagemaker_session,
                                epochs=15,
                                binary_classifier_model_selection_criteria='precision_at_target_recall',
                                target_recall=0.9
                               )


# %%
"""
### EXERCISE: Train the balanced estimator

Fit the new, balanced estimator on the formatted training data.
"""

# %%
%%time 
# train the estimator on formatted training data
linear_balanced.fit(formatted_train_data, wait=True, logs=True, job_name='fraud-detection-linear-balanced-6-5')

# %%
"""
### EXERCISE: Deploy and evaluate the balanced estimator

Deploy the balanced predictor and evaluate it. Do the results match with your expectations?
"""

# %%
%%time 
# deploy and create a predictor
balanced_predictor = linear.deploy(initial_instance_count=1, 
                                 instance_type='ml.t2.medium', 
                                 endpoint_name='fraud-detection-balanced-predictor', #same endpoint prividing the same name can not hold two estimators in this way.Use Multi-Model Endpoint notebook 
                                 wait=True,
                                 model_name='fraud-detection-balanced-predictor-06-05-2020')

# %%
print('Metrics for balanced, LinearLearner.\n')

# get metrics for balanced predictor
metrics = evaluate(balanced_predictor, 
                   test_features.astype('float32'), 
                   test_labels, 
                   verbose=True)

# %%
"""
## Delete the endpoint 

When you're done evaluating a model, you should delete the endpoint.
"""

# %%
# delete the predictor endpoint 
# delete_endpoint(balanced_predictor)

# %%
"""
A note on metric variability: 

The above model is tuned for the best possible precision with recall fixed at about 90%. The recall is fixed at 90% during training, but may vary when we apply our trained model to a test set of data.
"""

# %%
"""
---
## Model Design

Now that you've seen how to tune and balance a LinearLearner. Create, train and deploy your own model. This exercise is meant to be more open-ended, so that you get practice with the steps involved in designing a model and deploying it.

### EXERCISE: Train and deploy a LinearLearner with appropriate hyperparameters, according to the given scenario

**Scenario:**
* A bank has asked you to build a model that optimizes for a good user experience; users should only ever have up to about 15% of their valid transactions flagged as fraudulent.

This requires that you make a design decision: Given the above scenario, what metric (and value) should you aim for during training?

You may assume that performance on a training set will be within about 5-10% of the performance on a test set. For example, if you get 80% on a training set, you can assume that you'll get between about 70-90% accuracy on a test set.

Your final model should account for class imbalance and be appropriately tuned. 
"""

# %%
"""
* If we're allowed about 15/100 incorrectly classified valid transactions (false positives), then I can calculate an approximate value for the precision that I want as: 85/(85+15) = 85%. I'll aim for about 5% higher during training to ensure that I get closer to 80-85% precision on the test data.
"""

# %%
%%time
# instantiate and train a LinearLearner

# include params for tuning for higher precision
# *and* account for class imbalance in training data
# instantiate LinearLearner
linear_balanced_precision = LinearLearner(role=role,
                     instance_count=1,
                     instance_type='ml.c4.xlarge',
                     predictor_type='binary_classifier',
                     binary_classifier_model_selection_criteria='recall_at_target_precision',
                     target_precision=0.92,
                     positive_example_weight_mult='balanced',
                     epochs=20,
                     #init_method='normal', # weight initialization 
                     #init_sigma=stad_dev_train,
                     optimizer='sgd',
                     #loss='softmax_loss',
                     learning_rate='0.01',
                     normalize_data=True,
                     normalize_label=True,
                     #unbias_data=True,
                     #unbias_label=True,
                     early_stopping_patience=15,
                     max_run =60 * 60 * 2,  # max timeout of trainning in seconds - 2 hours
                     output_path= output_path,
                     sagemaker_session=sagemaker_session
                     )


# %%
%%time 
# train and deploy and evaluate a predictor
linear_balanced_precision.fit(formatted_train_data, wait=True, logs=False, job_name='fraud-detection-linear-balanced-precision-6-5-tune3')
predictor_linear_balanced_precision = linear_balanced_precision.deploy(initial_instance_count=1, 
                                 instance_type='ml.t2.medium', 
                                 endpoint_name='fraud-detection-linear-balanced-precision-tune3',
                                 wait=True,
                                 model_name='fraud-detection-linear-balanced-precision-06-05-2020-tune3')
print('Metrics for balanced, LinearLearner.\n')

# get metrics for balanced predictor
metrics = evaluate(predictor_linear_balanced_precision, 
                   test_features.astype('float32'), 
                   test_labels, 
                   verbose=True)

# %%
"""
---------------------!Metrics for balanced, LinearLearner

Without 

        init_method='normal', # weight initialization 
        init_sigma=stad_dev_train,


prediction (col)    0.0  1.0
actual (row)                
0.0               85278   24
1.0                  46   95

Recall:     0.674
Precision:  0.798
Accuracy:   0.999

CPU times: user 5.84 s, sys: 61.7 ms, total: 5.9 s
Wall time: 17min 43s

-----------------------------------------------------

"""

# %%
"""

-------------------------!Metrics for balanced, LinearLearner.

With parameters on training:

        init_method='normal', # weight initialization 
        init_sigma=stad_dev_train,
------------------------------------------------------------

prediction (col)    1.0
actual (row)           
0.0               85302
1.0                 141

Recall:     1.000
Precision:  0.002
Accuracy:   0.002

CPU times: user 5.86 s, sys: 29.5 ms, total: 5.89 s
Wall time: 18min 26s
"""

# %%
## IMPORTANT
# delete the predictor endpoint after evaluation 


# %%
"""
## Final Cleanup!

* Double check that you have deleted all your endpoints.
* I'd also suggest manually deleting your S3 bucket, models, and endpoint configurations directly from your AWS console.

You can find thorough cleanup instructions, [in the documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/ex1-cleanup.html).
"""

# %%
"""
---
# Conclusion

In this notebook, you saw how to train and deploy a LinearLearner in SageMaker. This model is well-suited for a binary classification task that involves specific design decisions and managing class imbalance in the training set.

Following the steps of a machine learning workflow, you loaded in some credit card transaction data, explored that data and prepared it for model training. Then trained, deployed, and evaluated several models, according to different design considerations!
"""