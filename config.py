import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'

    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    SQLALCHEMY_POOL_SIZE = 200
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SWAGGER = {
        "swagger_version": "2.0",
        "title": "NS",
        "specs": [
            {
                "version": "0.0.1",
                "title": "v1",
                "endpoint": 'v1_spec',
                "description": 'Northeastern Scheduler',
                "route": '/v1/spec',
            }
        ]
    }
    OAUTH_CREDENTIALS = {
        'facebook': {
            'id': '523775191157144',
            'secret': '20fa88dd03bc02e82acd6b62e7d8a306'
        }
    }

    # CELERY_BROKER_URL = 'redis://localhost:6379/0'
    # CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    # CELERYD_CONCURRENCY = 20

    CACHE_TYPE = 'redis'
    CACHE_KEY_PREFIX = 'f'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'

    OAUTH_CREDENTIALS = {
        'facebook': {
            'id': '523775191157144',
            'secret': '20fa88dd03bc02e82acd6b62e7d8a306'
        }
    }


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL_TEST']
