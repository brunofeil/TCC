# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 19:28:37 2022

@author: bruno
"""

import pandas as pd 
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

#!pip install plotly --upgrade

# Get data from postgresql
input_path = os.path.split(os.path.abspath("."))[0]+"\input"

# Import to make the analysis
df = pd.read_csv(input_path + '\dados.csv', sep=';')


df.drop(['course_id',
         'course_name',
         'student_id',
         'tarefas_disciplina',
         'posts_disciplina',
         'quizzes_disciplina'], axis='columns', inplace=True)

# Drop columns with no data (same data to all lines)
for column in df:
    if len(df[column].unique()) <= 1:
        df.drop([column], axis='columns', inplace=True)
        
# Filling NaN values
df.media_tempo_conclusao_quiz.fillna(df.media_tempo_conclusao_quiz.max()*2, inplace=True) #double of maximum quiz completion time
df.media_notas_quiz.fillna(0, inplace=True)

scaler_df = StandardScaler()
scaled_df = scaler_df.fit_transform(df)

kmeans_df = KMeans(n_clusters=2)
kmeans_df.fit(scaled_df)

centroides = scaler_df.inverse_transform(kmeans_df.cluster_centers_)


rotulos = kmeans_df.labels_
rotulos