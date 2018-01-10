# Northeastern Schedule API

To choose classes at Northeastern University, students use an internal tool to query for available classes and schedules based on certain criteria. These queries are quite simple and yet they take very to complete.

My project provides a way to scrape Northeastern's scheduling resources and a web service that allows for much faster and detailed querying. Everything is written in Python 3, using BeautifulSoup for parsing and Flask for the web service. I used PostgreSQL as my database. A Swagger service is also provided.
 
My project provides many features existing solutions do not: integration of professor ratings/information with classes, powerful queries that allow for customizable filters, full text search on class descriptions, and fast queries.

The frontend is still in development and the service is not running anywhere right now. However, you can run the backend on your own machine.

Everything is written in with Python 3

## Setup

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

    
    
