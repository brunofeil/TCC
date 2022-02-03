# -*- coding: utf-8 -*-
"""
Created on Mon Jan 31 20:28:16 2022

@author: bruno
"""


import pandas as pd 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
colormap = plt.cm.cool
import psycopg2

PGHOST='localhost'
PGDATABASE='postgres'
PGUSER='postgres'
PGPASSWORD=''
conn_string = "host="+ PGHOST +" port="+ "5432" +" dbname="+ PGDATABASE +" user=" + PGUSER +" password="+ PGPASSWORD


# Get data from postgresql
input_path = os.path.split(os.path.abspath("."))[0]+"\input"

str_query = """
select * from logs.flat_students
"""

conn=psycopg2.connect(conn_string)
cursor = conn.cursor()
cursor.execute(str_query)
result = cursor.fetchone()

dados = []

if result is None:
    print("Nenhum resultado")
else:
    while result:
        dados.append(result)
        result = cursor.fetchone()
cursor.close()
conn.close()

columns = [
        'course_id',
        'course_name',
        'student_id',
        'tarefas_disciplina',
        'tarefas_enviadas_pelo_aluno',
        'envios_em_dia',
        'envios_atrasados',
        'media_notas_tarefas',
        'posts_disciplina',
        'posts_criados_pelo_aluno',
        'posts_respondidos_pelo_aluno',
        'quizzes_disciplina',
        'quizzes_finalizados_pelo_aluno',
        'quizzes_atrasados_pelo_aluno',
        'quizzes_abandonados_pelo_aluno',
        'media_tempo_conclusao_quiz',
        'media_notas_quiz',
        'nota_final'
        ]

df_dados = pd.DataFrame(dados, columns = columns)
# Export to a csv file
df_dados.to_csv(input_path + '\dados.csv',
                sep = ';',
                index=False)


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
    print(column)
    if len(df[column].unique()) <= 1:
        df.drop([column], axis='columns', inplace=True)

# Pearson correlation
#Checking if there is continuous data that has a strong correlation with Person correlation
plt.figure(figsize=(18,16))
plt.title('Spearman correlation of continuous features', y=1.05, size=30)
sns.heatmap(df.corr(method='spearman'),linewidths=0.5,vmax=1.0, square=True, cmap=colormap, linecolor='white', annot=True)
