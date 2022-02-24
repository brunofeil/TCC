-- Staging
create table staging.tmp_courses
(
	course_id int,
	short_name varchar(10),
	full_name varchar(30)
)

select * from staging.tmp_courses

create table staging.tmp_users 
(
	course_id int,
	user_id int,
	user_role varchar(30),
	anonymized_id int
)

select * from staging.tmp_users

create table staging.tmp_assignments 
(
	assignment_id int,
	user_id int,
	attempt_number int,
	status varchar(30),
	time_created int, 
	time_modifier int,
	grading_status varchar(9),     
	due_date int
)

drop table staging.tmp_assignments

create table staging.tmp_forums 
(
	forum_id int,
	discussion_id int,
	discussion_created_by_id int,
	post_id int,
	post_user_id int,
	post_status varchar(8)
)

drop table staging.tmp_quizzes

create table staging.tmp_quizzes 
(
	quiz_id int,
	attempt_id int,
	user_id int,
	attempt_number int,
	status varchar(15),
	time_start int, 
	time_finish int, 
	sum_grades numeric(6,2),
	best_grade numeric(6,2)
)

create table staging.tmp_grades
(
	item_id int,
	user_id int,
	item_name varchar(100),
	item_type varchar(30),
	item_module varchar(30), 
	item_instance int, 
	grade numeric(8,2),
	grade_date int,
	max_grade numeric(8,2)
)

select * from staging.tmp_quizzes

-- Agregate
create table logs.courses
(
	course_id int,
	short_name varchar(10),
	full_name varchar(30)
)


create table logs.users 
(
	course_id int,
	user_id int,
	user_role varchar(30),
	anonymized_id int
)

create table logs.assignments 
(
	assignment_id int,
	user_id int,
	attempt_number int,
	status varchar(30),
	time_created int, 
	time_modifier int,
	grading_status varchar(9),     
	due_date int
)

create table logs.forums 
(
	forum_id int,
	discussion_id int,
	discussion_created_by_id int,
	post_id int,
	post_user_id int,
	post_status varchar(8)
)

drop table logs.quizzes 

create table logs.quizzes 
(
	quiz_id int,
	attempt_id int,
	user_id int,
	attempt_number int,
	status varchar(15),
	time_start int, 
	time_finish int,
	sum_grades numeric(6,2),
	best_grade numeric(6,2)
)

create table logs.grades
(
	item_id int,
	user_id int,
	item_name varchar(100),
	item_type varchar(30),
	item_module varchar(30), 
	item_instance int, 
	grade numeric(8,2),
	grade_date int,
	max_grade numeric(8,2)
)

--truncate table logs.quizzes

select * from logs.quizzes 

delete 
from logs.users u
using staging.tmp_users tu
where 1=1
  and u.user_id = tu.user_id 
  and u.course_id = tu.course_id
  
  
select staging.sp_staging_to_consolidate()


logs.courses
logs.users
logs.assignments

select * from logs.forums

logs.quizzes

-- Assignments
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

-- Foruns
select 
	u.user_id,
	(select count(distinct f_temp.post_id) from logs.forums f_temp) posts_disciplina,
	sum(case when f.post_status = 'creation' then 1 else 0 end) posts_criados,
	sum(case when f.post_status = 'response' then 1 else 0 end) posts_respondidos
from logs.forums f
right join logs.users u on u.user_id = f.post_user_id 
where u.user_role = 'student'
group by u.user_id

-- Quizzes
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

select *, time_finish - time_start 
from logs.quizzes q 
where user_id = 40

select user_id, max(best_grade), sum(case when q.attempt_number > 1 then 0 else best_grade end), sum(case when q.attempt_number > 1 then 0 else best_grade end) / count(distinct q.quiz_id) 
from logs.quizzes q 
where user_id = 36
group by user_id  

-- Grades

select
	user_id,
	max(g.grade) nota_final 
from logs.grades g
where g.item_type = 'course' and g.grade <> -1
group by user_id

select
	g.user_id,
	avg(g.grade) media_notas_tarefas
from logs.grades g 
where g.item_module = 'assign' and g.grade <> -1
group by g.user_id

select * from logs.assignments a 

-- Cria a flat
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
where u.user_role = 'student'


-- flat table 
-- staging 
create table staging.tmp_flat_students
(
	course_id int,
	course_name varchar(30),
	student_id int,
	tarefas_disciplina int,
	tarefas_enviadas_pelo_aluno int,
	envios_em_dia int,
	envios_atrasados int,
	media_notas_tarefas numeric(6,2),
	posts_disciplina int,
	posts_criados_pelo_aluno int,
	posts_respondidos_pelo_aluno int,
	quizzes_disciplina int, 
	quizzes_finalizados_pelo_aluno int,
	quizzes_atrasados_pelo_aluno int,
	quizzes_abandonados_pelo_aluno int,
	media_tempo_conclusao_quiz int8,
	media_notas_quiz numeric(6,2),
	nota_final numeric(6,2),
	primary key (course_id, student_id)
)


create table logs.flat_students
(
	course_id int,
	course_name varchar(30),
	student_id int,
	tarefas_disciplina int,
	tarefas_enviadas_pelo_aluno int,
	envios_em_dia int,
	envios_atrasados int,
	media_notas_tarefas numeric(6,2),
	posts_disciplina int,
	posts_criados_pelo_aluno int,
	posts_respondidos_pelo_aluno int,
	quizzes_disciplina int, 
	quizzes_finalizados_pelo_aluno int,
	quizzes_atrasados_pelo_aluno int,
	quizzes_abandonados_pelo_aluno int,
	media_tempo_conclusao_quiz int8,
	media_notas_quiz numeric(6,2),
	nota_final numeric(6,2),
	primary key (course_id, student_id)
)


select * from staging.tmp_flat_students