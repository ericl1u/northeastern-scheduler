#API for Northeastern courses, sechdules, and professors

Everything is written in with Python 3

Create a virtual environment:

    pip3 install virtualenv

Start virual environment:

    virtualenv env
    source env/bin/activate
    
Install requirements:

    pip install -r requirements.txt
    
Install postgresql. On macOS with Brew:

    brew install postgresql
    
Start postgresql and create databases;

    psql
    CREATE DATABASE $db_name;
    CREATE DATABASE $db_name_test;
    \q
    
Set environment variables:

    export APP_SETTINGS="config.DevelopmentConfig"
    
Database URLs are in the form:

    postgres://username:password@host/database
    
    DATABASE_URL=$db_name_url
    DATABASE_URL_TEST=$db_name_test_url

Initiate database schema:

    python3 db_create.py
    
Run tests:

    python3 tests.py
    
Fill database:

    http://localhost:5000/update/courses
    http://localhost:5000/update/schedules
    
To fill trace, log into MyNEU, get cookie and paste in

    http://localhost:5000/update/trace

Test API:

    python3 run.py
    http://localhost:5000/apidocs/index.html

    
    
