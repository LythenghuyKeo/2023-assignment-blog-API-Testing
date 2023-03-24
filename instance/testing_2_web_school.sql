select * from subject;
select * from role;
select * from post;
select * from department;
select name from _user;
SELECT * FROM pg_catalog.pg_tables
insert into subject (subject_name,department_id) values ('Introduction to Data Structure and Algorithm 101a',1);
select subject_name,department_name from department inner join subject on department.id=subject.department_id;
alter table public.user rename to _user;
drop table user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO postgres;
SELECT COLUMN_NAME  
FROM information_schema.COLUMNS  
WHERE TABLE_NAME = '_user';  
select * from profile;