import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = 'keyztracer'
    DEFAULT_CLIENT_IP = '172.16.136.205'
    DEFAULT_CLIENT_PORT = 1234
    DEFAULT_TIME_INT = 1
    DEFAULT_SAMPLE_SIZE = 120
    DEFAULT_PERF_TIME = 120
    DEFAULT_PERF_HZ = 49
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    STACK_DIR = 'app/static/perf'
    JSONIFY_PRETTYPRINT_REGULAR = False

    @staticmethod
    def init_app(app):
        pass

#定义使用的数据库路径
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
