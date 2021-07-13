import moodle_api
import pandas as pd

moodle_api.URL = "https://moodle.ufrgs.br/"
moodle_api.KEY = ""


def get_course_id():
    # Listar os cursos
    courses = moodle_api.call('core_course_get_courses')
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
    return course_id

def get_students_ids(course_id):
    # Pegar os alunos do curso
    users = moodle_api.call('core_enrol_get_enrolled_users', courseid = course_id)
    columns_names = ['CourseId', 'UserId', 'FullName', 'Role']
    users_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    for user in users:
        users_df.loc[df_index] = [
            course_id,
            user['id'],
            user['fullname'],
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
    submissions = moodle_api.call('mod_assign_get_submissions', assignmentids = assignments_list)
    submissions = submissions['assignments']
    columns_names = ['Assignment', 'UserId', 'AttemptNumber', 'Status', 'TimeCreated', 'TimeModifier', 'GradingStatus', 'DueDate']
    submissions_df = pd.DataFrame(columns=columns_names)
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

def get_forums(course_id):
    forums = moodle_api.call('mod_forum_get_forums_by_courses', courseids = [course_id]) 
    columns_names = ['ForumId', 'DiscussionId', 'DiscussionCreatedById', 'PostId', 'PostUserId', 'PostStatus']
    forums_df = pd.DataFrame(columns=columns_names)
    df_index = 1
    for forum in forums:
        discussions = moodle_api.call('mod_forum_get_forum_discussions ', forumid = forum['id'])['discussions']
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

if __name__ == '__main__':
    course_id = get_course_id()
    users_df = get_students_ids(course_id)
    get_assignments(course_id)
    get_forums(course_id)
    get_quizzes(course_id, users_df)