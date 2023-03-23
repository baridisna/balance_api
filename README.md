# Balance API

This API is build in python Django REST Framework

What need to be installed:
1. python minimal 3.8
2. PostgreSQL


How to install and run via virtualenv python:
1. make python virtualenv (python >3.8)
2. activate virtualenv
3. in virtualenv, type command `pip install -r requirements.txt`
4. make .env file from .env-example and setup credential database
5. migrate the database migration `python manage.py migrate`
6. run by command `python manage.py runserver`
7. to make superuser run this command `python manage.py createsuperuser`
   superuser doesn't have any user_balance and bank_balance
8. documentation API can be found at `localhost:8000/docs/` after login with username and password at `localhost:8000/admin/`
9. to create regular user `POST .../api/user/register/`