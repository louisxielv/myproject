Functions:
User Part:
1. register, login with email
2. change, reset password with email verification
3. edit profile

Recipe and reivew Part:
1. text input

Group Part:
1. create groups

need to do:
1. recipe photo tags ingredients




Role.insert_roles()
Tag.insert_tags()
u = User(email='nychent@gmail.com', username='chet', password='chet', confirmed=True)

README
How to run:
1. set a virtualenv and into it
2. install all requirments:
pip install -r requirements/dev
3. upgrade to current database use "python manage.py upgrade"
check the version using following 
(flasky) chet@chets-MBP ~/Projects/demo/myproject (chet●)$ python manage.py db current                                   [2.3.1]
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
08fcec18af7e (head)
4. python manage.py runserver
5. start 
