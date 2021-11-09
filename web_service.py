import moodle_api
import pandas as pd

import psycopg2

PGHOST='localhost'
PGDATABASE='postgres'
PGUSER='postgres'
PGPASSWORD='annelinda'
conn_string = "host="+ PGHOST +" port="+ "5432" +" dbname="+ PGDATABASE +" user=" + PGUSER +" password="+ PGPASSWORD


moodle_api.URL = ""
moodle_api.KEY = ""
cartao_ufrgs = ''

def get_course_id():
    # Listar os cursos
    webservice_user_id = moodle_api.call('core_user_get_users_by_field', field = 'username', values = [cartao_ufrgs])[0]['id'] 
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
    print()
    print(users_df)
    return users_df

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
        print()
        print(submissions_df)

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
    print()
    print(forums_df)
    return forums_df

def get_quizzes(course_id, users_df):
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
    for user_id in users_df.loc[users_df['Role'] == 'student']['UserId'].tolist():
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
    print()
    print(quizzes_df)
    return quizzes_df

def get_grades(course_id, users_df):
    columns_names = ['ItemId', 'UserId', 'ItemName', 'ItemType', 'ItemModule', 'ItemIsntance', 'Grade', 'DateGradeSubmitted', 'MaxGrade']
    grades_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    for user_id in users_df.loc[users_df['Role'] == 'student']['UserId'].tolist():
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
    print(grades_df)
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

    str_insert = "INSERT INTO staging.tmp_users (course_id, user_id, user_role) VALUES (%s, %s, %s)"
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
