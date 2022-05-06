import moodle_api
import pandas as pd
from random import randint
import psycopg2
import os
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree
from pandas_profiling import ProfileReport    

PGHOST='localhost'
PGDATABASE='postgres'
PGUSER='postgres'
PGPASSWORD='annelinda'
PORT = '5432'
conn_string = "host="+ PGHOST +" port="+ PORT +" dbname="+ PGDATABASE +" user=" + PGUSER +" password="+ PGPASSWORD

input_path = os.path.split(os.path.abspath("."))[0]+"\input"
output_path = os.path.split(os.path.abspath("."))[0]+"\output"
colormap = plt.cm.cool

moodle_api.URL = "http://localhost/" #"https://moodle.ufrgs.br/"
moodle_api.KEY = '8f90b66df0972a424f0f7765c19e721f'#"697e99200944982b60988fb3bae4bfca"#"4b9b988cc1d65e93b14baa86a62f0519"
user_name = 'professor_teste'#'professor_teste'#'web_service_user'

def get_course_id():
    # Listar os cursos
    webservice_user_id = moodle_api.call('core_user_get_users_by_field', field = 'username', values = [user_name])[0]['id'] 
    courses = moodle_api.call('core_enrol_get_users_courses', userid = webservice_user_id) 
    columns_names = ['CourseId', 'ShortName', 'FullName']
    courses_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    for course in courses:
        courses_df.loc[df_index] = [
            course['id'],
            course['shortname'],
            course['fullname']
        ]
        df_index += 1
    print()
    print(courses_df)

    while True:
        course_id = int(input('Escolha o curso pelo seu ID: '))
        if course_id in courses_df['CourseId'].tolist():
            break
    return course_id, courses_df

def get_students_ids(course_id):
    # Pegar os alunos do curso
    users = moodle_api.call('core_enrol_get_enrolled_users', courseid = course_id)
    columns_names = ['CourseId', 'UserId', 'Role']
    users_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    for user in users:
        users_df.loc[df_index] = [
            course_id,
            user['id'],
            #  user['fullname'],
            #  user['firstaccess'],
            #  user['lastaccess'],
            user['roles'][0]['shortname']
        ]
        df_index += 1
    users_df = anonymize_students_id(users_df)
    # print()
    # print(users_df)
    return users_df

def anonymize_students_id(u_df):
    """ 
        Created by Jéferson Guimarães (JefersonFG)

        Available on: https://github.com/JefersonFG/moodle-log-anonymizer
    """
    all_students_ids = u_df.loc[u_df['Role']=='student']['UserId']
    original_ids = set()
    original_ids
    original_ids.update(all_students_ids.unique())
    original_ids = list(original_ids)
    ids_dict = {key: str(randint(0, 99999)) for key in original_ids}
    u_df['AnonymizedId'] = u_df['UserId'].map(ids_dict)
    u_df['AnonymizedId'] = u_df['AnonymizedId'].fillna(u_df['UserId'])
    return u_df

def get_assignments(course_id):
    # Assignment
    # Pegar os ids de todas as assignments do curso
    assignments = moodle_api.call('mod_assign_get_assignments', courseids = [course_id])
    assignments = assignments['courses'][0]['assignments'] 
    columns_names = ['AssignmentId', 'DueDate']
    assignments_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    for assignment in assignments:
        assignments_df.loc[df_index] = [
            assignment['id'],
            assignment['duedate']
        ]
        df_index += 1
    assignments_list = assignments_df['AssignmentId'].tolist()

    # Pegar os envios e vizualizações das tarefas
    columns_names = ['Assignment', 'UserId', 'AttemptNumber', 'Status', 'TimeCreated', 'TimeModifier', 'GradingStatus', 'DueDate']
    submissions_df = pd.DataFrame(columns=columns_names)
    if len(assignments_list) > 0:
        submissions = moodle_api.call('mod_assign_get_submissions', assignmentids = assignments_list)
        submissions = submissions['assignments']
        # columns_names = ['Assignment', 'UserId', 'AttemptNumber', 'Status', 'TimeCreated', 'TimeModifier', 'GradingStatus', 'DueDate']
        # submissions_df = pd.DataFrame(columns=columns_names)
        df_index = 1
        for submission in submissions:
            for submission_attempt in submission['submissions']:
                submissions_df.loc[df_index] = [
                    submission['assignmentid'], 
                    submission_attempt['userid'], 
                    submission_attempt['attemptnumber'], 
                    submission_attempt['status'], 
                    submission_attempt['timecreated'], 
                    submission_attempt['timemodified'], 
                    submission_attempt['gradingstatus'],
                    assignments_df.loc[assignments_df['AssignmentId'] == submission['assignmentid']]['DueDate'].values[0]
                ]
                df_index += 1
        # print()
        # print(submissions_df)

    return submissions_df

def get_forums(course_id):
    forums = moodle_api.call('mod_forum_get_forums_by_courses', courseids = [course_id]) 
    columns_names = ['ForumId', 'DiscussionId', 'DiscussionCreatedById', 'PostId', 'PostUserId', 'PostStatus']
    forums_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    for forum in forums:
        discussions = moodle_api.call('mod_forum_get_forum_discussions', forumid = forum['id'])['discussions']
        for discussion in discussions:
                discussion_id = discussion['discussion']
                discussion_created_by = discussion['userid']
                posts = moodle_api.call('mod_forum_get_discussion_posts', discussionid  = discussion['discussion'])['posts']
                for post in posts:
                    post_id = post['id']
                    post_userd_id = post['author']['id']
                    post_status = 'response' if post['hasparent'] else 'creation'
                    forums_df.loc[df_index] = [
                        forum['id'],
                        discussion['discussion'],
                        discussion['userid'],
                        post['id'],
                        post['author']['id'],
                        'response' if post['hasparent'] else 'creation'
                    ]
                    df_index += 1
    # print()
    # print(forums_df)
    return forums_df

def get_quizzes(course_id, u_df):
    # Quiz
    # Pegar os ids de todos os quizes
    quizzes = moodle_api.call('mod_quiz_get_quizzes_by_courses', courseids = [course_id])['quizzes']
    columns_names = ['QuizId', 'AttemptId', 'UserId', 'AttemptNumber', 'Status', 'TimeStart', 'TimeFinish', 'SumGrades', 'BestGrade']
    quizzes_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    quizzes_ids = []
    for quiz in quizzes:
        quizzes_ids.append(quiz['id'])

    # Para cada aluno do curso, pegar as tentativas de resolução dos quizzes
    for user_id in u_df.loc[u_df['Role'] == 'student']['UserId'].tolist():
        for quiz_id in quizzes_ids:
            attempts = moodle_api.call('mod_quiz_get_user_attempts', quizid = quiz_id, userid = user_id)['attempts']
            quiz_best_grade = moodle_api.call('mod_quiz_get_user_best_grade', quizid = quiz_id, userid = user_id)
            for attempt in attempts:
                quizzes_df.loc[df_index] = [
                    quiz_id,
                    attempt['id'],
                    attempt['userid'],
                    attempt['attempt'],
                    attempt['state'],
                    attempt['timestart'],
                    attempt['timefinish'],
                    attempt['sumgrades'],
                    quiz_best_grade['grade'] if quiz_best_grade['hasgrade'] else -1
                ]
                df_index += 1
    # print()
    # print(quizzes_df)
    return quizzes_df

def get_grades(course_id, u_df):
    columns_names = ['ItemId', 'UserId', 'ItemName', 'ItemType', 'ItemModule', 'ItemIsntance', 'Grade', 'DateGradeSubmitted', 'MaxGrade']
    grades_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    for user_id in u_df.loc[u_df['Role'] == 'student']['UserId'].tolist():
        grades = moodle_api.call('gradereport_user_get_grade_items', courseid = course_id, userid = user_id)['usergrades'][0]['gradeitems']
        for grade in grades:
            if grade['itemtype'] != 'category':
                grades_df.loc[df_index] = [
                        grade['id'],
                        user_id,                    
                        grade['itemname'],
                        grade['itemtype'],
                        grade['itemmodule'],
                        grade['iteminstance'],
                        grade['graderaw'] if grade['graderaw'] is not None else -1,
                        grade['gradedatesubmitted'],
                        grade['grademax']
                    ]
                df_index += 1
    # print(grades_df)
    return grades_df

def import_courses(c_df):
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Criar um "create_insert"

    str_insert = "INSERT INTO staging.tmp_courses (course_id, short_name, full_name) VALUES (%s, %s, %s)"
    str_truncate = "TRUNCATE TABLE staging.tmp_courses"

    cursor.execute(str_truncate)

    if c_df.size > 0:
        for i, row in c_df.iterrows():
            cursor.execute(str_insert, tuple(row))
    conn.commit()
    conn.close()

def import_users(u_df):
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Criar um "create_insert"

    str_insert = "INSERT INTO staging.tmp_users (course_id, user_id, user_role, anonymized_id) VALUES (%s, %s, %s, %s)"
    str_truncate = "TRUNCATE TABLE staging.tmp_users"

    cursor.execute(str_truncate)

    if u_df.size > 0:
        for i, row in u_df.iterrows():
            cursor.execute(str_insert, tuple(row))
    conn.commit()
    conn.close()

def import_assignments(a_df):
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Criar um "create_insert"

    str_insert = "INSERT INTO staging.tmp_assignments (assignment_id, user_id, attempt_number, status, time_created, time_modifier, grading_status, due_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    str_truncate = "TRUNCATE TABLE staging.tmp_assignments"

    cursor.execute(str_truncate)

    if a_df.size > 0:
        for i, row in a_df.iterrows():
            cursor.execute(str_insert, tuple(row))
    conn.commit()
    conn.close()

def import_foruns(f_df):
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Criar um "create_insert"

    str_insert = "INSERT INTO staging.tmp_forums (forum_id, discussion_id, discussion_created_by_id, post_id, post_user_id, post_status) VALUES (%s, %s, %s, %s, %s, %s)"
    str_truncate = "TRUNCATE TABLE staging.tmp_forums"

    cursor.execute(str_truncate)
    if f_df.size > 0:
        for i, row in f_df.iterrows():
            cursor.execute(str_insert, tuple(row))
    conn.commit()
    conn.close()

def import_quizzes(q_df):
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Criar um "create_insert"

    str_insert = "INSERT INTO staging.tmp_quizzes (quiz_id, attempt_id, user_id, attempt_number, status, time_start, time_finish, sum_grades, best_grade) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    str_truncate = "TRUNCATE TABLE staging.tmp_quizzes"

    cursor.execute(str_truncate)

    if q_df.size > 0:
        for i, row in q_df.iterrows():
            cursor.execute(str_insert, tuple(row))
    conn.commit()
    conn.close()

def import_grades(g_df):
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Criar um "create_insert"

    str_insert = "INSERT INTO staging.tmp_grades (item_id, user_id, item_name, item_type, item_module,  item_instance,  grade, grade_date, max_grade) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    str_truncate = "TRUNCATE TABLE staging.tmp_grades"

    cursor.execute(str_truncate)

    if g_df.size > 0:
        for i, row in g_df.iterrows():
            cursor.execute(str_insert, tuple(row))
    conn.commit()
    conn.close()

def consolidate():
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()
    str_function_call = "select staging.sp_staging_to_consolidate()"
    cursor.execute(str_function_call)
    conn.commit()
    conn.close()

def import_flat():
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Criar um "create_insert"

    str_insert = """
    INSERT INTO staging.tmp_flat_students (course_id, course_name, student_id, tarefas_disciplina, tarefas_enviadas_pelo_aluno, envios_em_dia, envios_atrasados, media_notas_tarefas, posts_disciplina, posts_criados_pelo_aluno, posts_respondidos_pelo_aluno, quizzes_disciplina, quizzes_finalizados_pelo_aluno, quizzes_atrasados_pelo_aluno, quizzes_abandonados_pelo_aluno, media_tempo_conclusao_quiz, media_notas_quiz, nota_final)
    select
        c.course_id,
        c.full_name course_name,
        u.anonymized_id student_id,
        a.tarefas_disciplina,
        a.tarefas_enviadas tarefas_enviadas_pelo_aluno,
        a.envios_em_dia,
        a.envios_atrasados,
        (case when g_tarefas.media_notas_tarefas is null then -1 else g_tarefas.media_notas_tarefas end) media_notas_tarefas,
        f.posts_disciplina,
        f.posts_criados posts_criados_pelo_aluno,
        f.posts_respondidos posts_respondidos_pelo_aluno,
        q.quizzes_disciplina,
        q.quizzes_finalizados quizzes_finalizados_pelo_aluno,
        q.quizzes_atrasados quizzes_atrasados_pelo_aluno,
        q.quizzes_abandonados quizzes_abandonados_pelo_aluno,
        q.media_tempo_conclusao media_tempo_conclusao_quiz,
        q.media_notas media_notas_quiz,
        (case when g_final.nota_final is null then -1 else g_final.nota_final end) nota_final
    from logs.courses c
    join logs.users u on u.course_id = c.course_id 
    join 
    (
        select 
            user_id,
            tarefas_disciplina,
            sum(case when envio < 0 then 1 else 0 end) envios_atrasados,
            sum(case when envio >= 0 then 1 else 0 end) envios_em_dia,
            count(distinct assignment_id) tarefas_enviadas
        from 
        (
        select 
            u.user_id,
            a.assignment_id,
            (select count(distinct a_temp.assignment_id) from logs.assignments a_temp) tarefas_disciplina,
            a.due_date - a.time_modifier envio
        from logs.assignments a
        right join logs.users u on u.user_id = a.user_id 
        where u.user_role = 'student'
        ) t
        group by user_id, tarefas_disciplina
    ) a on a.user_id = u.user_id 
    join
    (
        select 
            u.user_id,
            (select count(distinct f_temp.post_id) from logs.forums f_temp) posts_disciplina,
            sum(case when f.post_status = 'creation' then 1 else 0 end) posts_criados,
            sum(case when f.post_status = 'response' then 1 else 0 end) posts_respondidos
        from logs.forums f
        right join logs.users u on u.user_id = f.post_user_id 
        where u.user_role = 'student'
        group by u.user_id
    ) f on f.user_id = u.user_id 
    join 
    (
        select 
            u.user_id,
            (select count(distinct q_temp.quiz_id) from logs.quizzes q_temp) quizzes_disciplina,
            max(q.attempt_number) nro_maximo_tentativas,
            sum(case when q.status = 'finished' then 1 else 0 end) quizzes_finalizados,
            sum(case when q.status = 'overdue' then 1 else 0 end) quizzes_atrasados,
            sum(case when q.status = 'abandoned' then 1 else 0 end) quizzes_abandonados,
            sum(q.time_finish - q.time_start)/count(1) media_tempo_conclusao,
            round(sum(case when q.attempt_number > 1 then 0 else best_grade end) / count(distinct q.quiz_id),2) media_notas
        from logs.quizzes q 
        right join logs.users u on u.user_id = q.user_id 
        where u.user_role = 'student'
        group by u.user_id 
    ) q on q.user_id = u.user_id 
    left join
    (
        select
            user_id,
            max(g.grade) nota_final 
        from logs.grades g
        where g.item_type = 'course' and g.grade <> -1
        group by user_id
    ) g_final on g_final.user_id = u.user_id 
    left join
    (
        select
            g.user_id,
            round(avg(g.grade), 2) media_notas_tarefas
        from logs.grades g 
        where g.item_module = 'assign' and g.grade <> -1
        group by g.user_id
    ) g_tarefas on g_tarefas.user_id = u.user_id 
    where u.user_role = 'student'"""
    str_truncate = "TRUNCATE TABLE staging.tmp_flat_students"

    cursor.execute(str_truncate)
    cursor.execute(str_insert)
    conn.commit()
    conn.close()

def update_flat():
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()
    str_function_call = "select staging.sp_update_flat()"
    cursor.execute(str_function_call)
    conn.commit()
    conn.close()

def get_data_from_postgresql(c_id):

    str_query = """
    select * from logs.flat_students where course_id = @COURSE_ID
    """
    conn=psycopg2.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute(str_query.replace('@COURSE_ID', str(c_id)))
    result = cursor.fetchone()

    data = []

    if result is None:
        print("Nenhum resultado")
    else:
        while result:
            data.append(result)
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

    df = pd.DataFrame(data, columns = columns)
    # Export to a csv file
    csv_path = input_path + '\data_course_' + str(c_id) + '.csv'
    df.to_csv(csv_path, sep=';', index=False)

    return csv_path

def correlation_analysis(csv_path, c_id):
    # Import to make the analysis
    df = pd.read_csv(csv_path, sep=';')

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

    corr_path = output_path + '\correlation_course_' + str(c_id) + '.png'

    # Spearman correlation
    # Checking if there is data that has a strong correlation with Spearman correlation
    plt.figure(figsize=(20,18))
    plt.title('Spearman correlation', y=1.05, size=30)
    correlation = sns.heatmap(df.corr(method='spearman'),linewidths=0.5,vmax=1.0, square=True, cmap=colormap, linecolor='white', annot=True)
    fig = correlation.get_figure()
    fig.savefig(corr_path) 

def clustering_analysis(csv_path, c_id):
    # Import to make the analysis
    df = pd.read_csv(csv_path, sep=';')
    
    original_df = df.copy()

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
    if 'media_tempo_conclusao_quiz' in df.columns:
        df.media_tempo_conclusao_quiz.fillna(df.media_tempo_conclusao_quiz.max()*2, inplace=True) #double of maximum quiz completion time
    if 'media_notas_quiz' in df.columns:
        df.media_notas_quiz.fillna(0, inplace=True)

    scaler_df = StandardScaler()
    scaled_df = scaler_df.fit_transform(df)
    kmeans_df = KMeans(n_clusters=2)
    kmeans_df.fit(scaled_df)
    centroids = scaler_df.inverse_transform(kmeans_df.cluster_centers_)
    clusters = kmeans_df.labels_
    original_df['cluster'] = clusters

    cluster_path = output_path + '\clustering_course_' + str(c_id)
    original_df.to_excel(cluster_path + '.xlsx', index=False) 

    # Export exploratory analysis

    original_df.drop(['course_id',
                    'course_name',
                    'student_id',
                    'tarefas_disciplina',
                    'posts_disciplina',
                    'quizzes_disciplina'], axis='columns', inplace=True)

    # Drop columns with no data (same data to all lines)
    for column in original_df:
        if len(original_df[column].unique()) <= 1:
            original_df.drop([column], axis='columns', inplace=True)    

    for cl in original_df.cluster.unique():
        clustered_df = original_df.loc[original_df.cluster == cl].copy()
        clustered_df.reset_index(drop=True, inplace=True)
        profile = ProfileReport(clustered_df, title='Course ' + str(c_id) + ' Cluster - ' + str(cl)) 
        profile.to_file(cluster_path + '_cluster_' + str(cl) + '.html')

def decision_trees(csv_path, c_id):
    # Import to make the analysis
    df = pd.read_csv(csv_path, sep=';')

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
    if 'media_tempo_conclusao_quiz' in df.columns:
        df.media_tempo_conclusao_quiz.fillna(df.media_tempo_conclusao_quiz.max()*2, inplace=True) #double of maximum quiz completion time
    if 'media_notas_quiz' in df.columns:
        df.media_notas_quiz.fillna(0, inplace=True)
    
    decisionT_df = df.copy()
    y_decisionT = decisionT_df.iloc[:, 1].values # class: envios_em_dia
    y_decisionT = y_decisionT.astype(str)

    # delete tarefas_enviadas_pelo_aluno if equals to envios_em_dia
    envios_em_dia_equals_todos_envios = decisionT_df.tarefas_enviadas_pelo_aluno.values == decisionT_df.envios_em_dia.values
    if envios_em_dia_equals_todos_envios.all():
       decisionT_df.drop(['envios_em_dia', 'tarefas_enviadas_pelo_aluno'], axis='columns', inplace=True)
    else:
       decisionT_df.drop(['envios_em_dia'], axis='columns', inplace=True)

    X_decisionT = decisionT_df.values
    decisionT = DecisionTreeClassifier(criterion='entropy')
    decisionT.fit(X_decisionT, y_decisionT)

    X = decisionT_df.columns
    figure, axis = plt.subplots(nrows=1, ncols=1, figsize=(24,24))
    tree.plot_tree(decisionT, feature_names=X, class_names = decisionT.classes_, filled=True)

    tree_path = output_path + r'\tree_course_' + str(c_id) + '.png'

    figure.savefig(tree_path)

if __name__ == '__main__':
    course_id, courses_df = get_course_id()
    users_df = get_students_ids(course_id)
    assignments_df = get_assignments(course_id)
    foruns_df = get_forums(course_id)
    quizzes_df = get_quizzes(course_id, users_df)
    grades_df = get_grades(course_id, users_df)
    import_courses(courses_df)
    import_users(users_df)
    import_assignments(assignments_df)
    import_foruns(foruns_df)
    import_quizzes(quizzes_df)
    import_grades(grades_df)
    consolidate()
    import_flat()
    update_flat()

    csv_path = get_data_from_postgresql(course_id)

    correlation_analysis(csv_path, course_id)

    decision_trees(csv_path, course_id)

    clustering_analysis(csv_path, course_id)

