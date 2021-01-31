#!/usr/bin/env python
# coding: utf-8

# In[1]:



#importing all the libraries and installing the new one's 

import re
import nltk
import time
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import KFold
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import confusion_matrix
from sklearn import preprocessing
from sklearn import utils
from imblearn.over_sampling import SMOTE
import joblib


# In[ ]:




def normalizer(user): #cleaning the data 
    soup = BeautifulSoup(user, 'lxml')  # please run 'pip install lxml' to make this line work; # removing HTML encoding such as ‘&amp’,’&quot’ or html tags such as '&gt'
    souped = soup.get_text()
    re1 = re.sub(r"(?:\@|http?\://|https?\://|www)\S+", " ", souped) # removing @mentions and urls
    re2 = re.sub("[^A-Za-z]+"," ", re1) # remove numbers

    """
    For more info on regular expressions visit -
    https://docs.python.org/3/library/re.html
    """

    tokens = nltk.word_tokenize(re2)
    removed_letters = [word for word in tokens if len(word)>2] # removing words with length less than or equal to 2
    lower_case = [l.lower() for l in removed_letters]

    stop_words = set(stopwords.words('english'))
    filtered_result = list(filter(lambda l: l not in stop_words, lower_case))

    wordnet_lemmatizer = WordNetLemmatizer()
    lemmas = [wordnet_lemmatizer.lemmatize(t, pos='v') for t in filtered_result]
    return lemmas

def Cross_validation(data, targets, clf_cv, model_name): ## to  Perform cross-validation on SVC

    kf = KFold(n_splits=10, shuffle=True, random_state=1) # 10-fold cross-validation
    scores=[]
    data_train_list = []
    targets_train_list = []
    data_test_list = []
    targets_test_list = []
    iteration = 0
    print("Performing cross-validation for {}...".format(model_name))
    for train_index, test_index in kf.split(data):
        iteration += 1
        print("Iteration ", iteration)
        data_train_cv, targets_train_cv = data[train_index], targets[train_index]
        data_test_cv, targets_test_cv = data[test_index], targets[test_index]
        data_train_list.append(data_train_cv) # appending training data for each iteration
        data_test_list.append(data_test_cv) # appending test data for each iteration
        targets_train_list.append(targets_train_cv) # appending training targets for each iteration
        targets_test_list.append(targets_test_cv) # appending test targets for each iteration
        clf_cv.fit(data_train_cv, targets_train_cv) # Fitting the SVC model
        score = clf_cv.score(data_test_cv, targets_test_cv) # Calculating accuracy
        print("Cross-validation accuracy: ", score)
        scores.append(score) # appending cross-validation accuracy for each iteration
    mean_accuracy = np.mean(scores)
    print("Mean cross-validation accuracy for {}: ".format(model_name), mean_accuracy)
    print("Best cross-validation accuracy for {}: ".format(model_name), max(scores))
    max_acc_index = scores.index(max(scores)) # best cross-validation accuracy
    max_acc_data_train = data_train_list[max_acc_index] # training data corresponding to best cross-validation accuracy
    max_acc_data_test = data_test_list[max_acc_index] # test data corresponding to best cross-validation accuracy
    max_acc_targets_train = targets_train_list[max_acc_index] # training targets corresponding to best cross-validation accuracy
    max_acc_targets_test = targets_test_list[max_acc_index] # test targets corresponding to best cross-validation accuracy

    return mean_accuracy, max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test


# In[ ]:




def c_matrix(max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test, targets, clf, model_name):
    clf.fit(max_acc_data_train, max_acc_targets_train) # Classifier fitting 
    targets_pred = clf.predict(max_acc_data_test) # Prediction on test data
    conf_mat = confusion_matrix(max_acc_targets_test, targets_pred)
    sns.heatmap(conf_mat, annot=True)
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.title("Confusion Matrix (Best Accuracy) - {}".format(model_name))
    plt.show()
    print('Confusion matrix: \n', conf_mat)
    print('TP: ', conf_mat[1,1])
    print('TN: ', conf_mat[0,0])
    print('FP: ', conf_mat[0,1])
    print('FN: ', conf_mat[1,0])


# In[ ]:




def main():
    ## to Read the training dataset as dataframe
    df = pd.read_csv("user_reviews.csv", encoding = "ISO-8859-1")
    pd.set_option('display.max_colwidth', -1) 
    # Converting  the Categorical features into Numerical features
    def converter(value):
        if value >= 8:
            return 1
        else:
            return 0

    df['score'] = df['score'].apply(converter)
    df['Recommendation']= df['score']

    ## now, Normalizing the reviews
    df['normalized_extract'] = df.extract.apply(normalizer)
    df = df[df['normalized_extract'].map(len) > 0] # removing rows with normalized reviews of length 0
    print("Printing top 5 rows of dataframe showing original and cleaned reviews....")
    print(df[['extract','normalized_extract']].head())
    df.drop(['source', 'domain', 'score_max', 'extract', 'product'], axis=1, inplace=True)
    #### Saving cleaned reviews to a diffetent csv
    df.to_csv('Cleaned_userReviews.csv', encoding='utf-8', index=False)
    ## Reading cleaned reviews as a new frame 
    cleaned_data = pd.read_csv("Cleaned_userReviews.csv", encoding = "ISO-8859-1")
    pd.set_option('display.max_colwidth', -1)
    data = cleaned_data.normalized_extract
    targets = cleaned_data.score
    tfidf = TfidfVectorizer(min_df=10, ngram_range=(1,1)) 
    tfidf.fit(data) 
    data = tfidf.transform(data) 
    pd.DataFrame.from_dict(data=dict([word, i] for i, word in enumerate(tfidf.get_feature_names())), orient='index').to_csv('vocabulary.csv', header=False)
    print("Shape of tfidf matrix: ", data.shape)
    
    ## Implementing SMOTE 
    print("Number of observations in each class before oversampling: \n", pd.Series(targets).value_counts())

    smote = SMOTE(random_state = 101)
    data,targets = smote.fit_sample(data,targets)

    print("Number of observations in each class after oversampling: \n", pd.Series(targets).value_counts())

    SVC_clf = LinearSVC() #making SVC Model
    SVC_mean_accuracy, max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test = Cross_validation(data, targets, SVC_clf, "SVC") # SVC cross-validation
    c_matrix(max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test, targets, SVC_clf, "SVC") # SVC confusion matrix

    NBC_clf = MultinomialNB() #making NBC Model
    NBC_mean_accuracy, max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test = Cross_validation(data, targets, NBC_clf, "NBC") # NBC cross-validation
    c_matrix(max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test, targets, NBC_clf, "NBC") # NBC confusion matrix

    #Tuning the random forest parameter 'n_estimators' and implementing cross-validation using Grid Search
    adaboost= AdaBoostClassifier(random_state=1)
    grid_param = {'n_estimators' : [400]}
    gd_sr = GridSearchCV(estimator=adaboost, param_grid=grid_param, scoring='accuracy', cv=10)
    gd_sr.fit(data,targets)
    best_parameters = gd_sr.best_params_
    print(best_parameters)
    best_result = gd_sr.best_score_
    print(best_result)
    
    if SVC_mean_accuracy > NBC_mean_accuracy:
        clf = LinearSVC().fit(data, targets)
        joblib.dump(clf, 'svc.sav')
    elif NBC_mean_accuracy > gd_sr_best_score_:
        clf = MultinomialNB().fit(data, targets)
        joblib.dump(clf, 'nbc.sav')
    else:
        clf = AdaBoosrClassifier().fit(data, targets)
        joblib.dump(clf, 'adb.sav')

if __name__ == "__main__":
    main()


# In[ ]:




def main():
    #### Reading training dataset as dataframe
    df = pd.read_csv("user_reviews.csv", encoding = "ISO-8859-1")
    pd.set_option('display.max_colwidth', -1) # Setting this so we can see the full content of cells
    # Converting Categorical features into Numerical features
    def converter(value):
        if value >= 8:
            return 1
        else:
            return 0

    df['score'] = df['score'].apply(converter)
    df['Recommendation']= df['score']

    #### Normalizing reviews
    df['normalized_extract'] = df.extract.apply(normalizer)
    df = df[df['normalized_extract'].map(len) > 0] # removing rows with normalized reviews of length 0
    print("Printing top 5 rows of dataframe showing original and cleaned reviews....")
    print(df[['extract','normalized_extract']].head())
    df.drop(['source', 'domain', 'score_max', 'extract', 'product'], axis=1, inplace=True)
    #### Saving cleaned reviews to csv
    df.to_csv('Cleaned_userReviews.csv', encoding='utf-8', index=False)
    #### Reading cleaned reviews as dataframe
    cleaned_data = pd.read_csv("Cleaned_userReviews.csv", encoding = "ISO-8859-1")
    pd.set_option('display.max_colwidth', -1)
    data = cleaned_data.normalized_extract
    targets = cleaned_data.score
    tfidf = TfidfVectorizer(min_df=20, ngram_range=(1,2)) 
    tfidf.fit(data) 
    data = tfidf.transform(data) 
    pd.DataFrame.from_dict(data=dict([word, i] for i, word in enumerate(tfidf.get_feature_names())), orient='index').to_csv('vocabulary.csv', header=False)
    print("Shape of tfidf matrix: ", data.shape)
    
    print("Number of observations in each class before oversampling: \n", pd.Series(targets).value_counts())

    smote = SMOTE(random_state = 101)
    data,targets = smote.fit_sample(data,targets)

    print("Number of observations in each class after oversampling: \n", pd.Series(targets).value_counts())

    SVC_clf = LinearSVC() 
    SVC_mean_accuracy, max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test = Cross_validation(data, targets, SVC_clf, "SVC") # SVC cross-validation
    c_matrix(max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test, targets, SVC_clf, "SVC") # SVC confusion matrix

    NBC_clf = MultinomialNB() 
    NBC_mean_accuracy, max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test = Cross_validation(data, targets, NBC_clf, "NBC") # NBC cross-validation
    c_matrix(max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test, targets, NBC_clf, "NBC") # NBC confusion matrix

    adaboost= AdaBoostClassifier(random_state=1)
    grid_param = {'n_estimators' : [500]}
    gd_sr = GridSearchCV(estimator=adaboost, param_grid=grid_param, scoring='accuracy', cv=10)
    gd_sr.fit(data,targets)
    best_parameters = gd_sr.best_params_
    print(best_parameters)
    best_result = gd_sr.best_score_
    print(best_result)
    
    if SVC_mean_accuracy > NBC_mean_accuracy:
        clf = LinearSVC().fit(data, targets)
        joblib.dump(clf, 'svc2.sav')
    elif NBC_mean_accuracy > gd_sr_best_score_:
        clf = MultinomialNB().fit(data, targets)
        joblib.dump(clf, 'nbc2.sav')
    else:
        clf = AdaBoosrClassifier().fit(data, targets)
        joblib.dump(clf, 'adb2.sav')

if __name__ == "__main__":
    main()


# In[ ]:



def main():
    df = pd.read_csv("user_reviews.csv", encoding = "ISO-8859-1")
    pd.set_option('display.max_colwidth', -1) 
    def converter(value):
        if value >= 8:
            return 1
        else:
            return 0

    df['score'] = df['score'].apply(converter)
    df['Recommendation']= df['score']

    #### Normalizing reviews
    df['normalized_extract'] = df.extract.apply(normalizer)
    df = df[df['normalized_extract'].map(len) > 0] # removing rows with normalized reviews of length 0
    print("Printing top 5 rows of dataframe showing original and cleaned reviews....")
    print(df[['extract','normalized_extract']].head())
    df.drop(['source', 'domain', 'score_max', 'extract', 'product'], axis=1, inplace=True)
    #### Saving cleaned reviews to csv
    df.to_csv('Cleaned_userReviews.csv', encoding='utf-8', index=False)
    #### Reading cleaned reviews as dataframe
    cleaned_data = pd.read_csv("Cleaned_userReviews.csv", encoding = "ISO-8859-1")
    pd.set_option('display.max_colwidth', -1)
    data = cleaned_data.normalized_extract
    targets = cleaned_data.score
    tfidf = TfidfVectorizer(min_df=30, ngram_range=(1,3)) 
    tfidf.fit(data) s
    data = tfidf.transform(data) 
    pd.DataFrame.from_dict(data=dict([word, i] for i, word in enumerate(tfidf.get_feature_names())), orient='index').to_csv('vocabulary.csv', header=False)
    print("Shape of tfidf matrix: ", data.shape)
    
    print("Number of observations in each class before oversampling: \n", pd.Series(targets).value_counts())

    smote = SMOTE(random_state = 101)
    data,targets = smote.fit_sample(data,targets)

    print("Number of observations in each class after oversampling: \n", pd.Series(targets).value_counts())

    SVC_clf = LinearSVC() 
    SVC_mean_accuracy, max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test = Cross_validation(data, targets, SVC_clf, "SVC") # SVC cross-validation
    c_matrix(max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test, targets, SVC_clf, "SVC") # SVC confusion matrix

    NBC_clf = MultinomialNB() 
    NBC_mean_accuracy, max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test = Cross_validation(data, targets, NBC_clf, "NBC") # NBC cross-validation
    c_matrix(max_acc_data_train, max_acc_data_test, max_acc_targets_train, max_acc_targets_test, targets, NBC_clf, "NBC") # NBC confusion matrix

    Adaboost= AdaBoostClassifier(random_state=1)
    grid_param = {'n_estimators' : [400]}
    gd_sr = GridSearchCV(estimator=Adaboost, param_grid=grid_param, scoring='accuracy', cv=10)
    gd_sr.fit(data,targets)
    best_parameters = gd_sr.best_params_
    print(best_parameters)
    best_result = gd_sr.best_score_
    print(best_result)
    
    if SVC_mean_accuracy > NBC_mean_accuracy:
        clf = LinearSVC().fit(data, targets)
        joblib.dump(clf, 'svc3.sav')
    elif NBC_mean_accuracy > gd_sr_best_score_:
        clf = MultinomialNB().fit(data, targets)
        joblib.dump(clf, 'nbc3.sav')
    else:
        clf = AdaBoosrClassifier().fit(data, targets)
        joblib.dump(clf, 'adb3.sav')

if __name__ == "__main__":
    main()

