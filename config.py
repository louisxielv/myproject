import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SSL_DISABLE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'cookzilla.project@gmail.com'  # os.environ.get('MAIL_USERNAME') or
    MAIL_PASSWORD = 'dbproject2016'  # os.environ.get('MAIL_PASSWORD') or
    COOKZILLA_MAIL_SUBJECT_PREFIX = '[Cookzilla]'
    COOKZILLA_MAIL_SENDER = 'Cookzilla Project <cookzilla.project@gmail.com>'
    # admin
    COOKZILLA_ADMIN = ['nychent@gmail.com']  # os.environ.get('COOKZILLA_ADMIN') or
    # pagination
    COOKZILLA_POSTS_PER_PAGE = 20
    COOKZILLA_FOLLOWERS_PER_PAGE = 50
    COOKZILLA_COMMENTS_PER_PAGE = 10
    COOKZILLA_SLOW_DB_QUERY_TIME = 0.5
    # the number of Ingredient
    INGREDIENT_NUMBER = 5
    # unit
    INGREDIENT_CONVERSION = {'pound(lb)': 2.205,
                             'ounce(oz)': 35.27,
                             'pint(pt)': 5.032,
                             'fluid ounce(fl oz)': 80.51,
                             'cup': 10.06,
                             'tablespoon': 161,
                             'dessert spoon': 241.5,
                             'teaspoon': 483.1,
                             'kilogram(kg)': 1,
                             'gram(g)': 1000,
                             'liter(l)': 2.381,
                             'deciliter(dl)': 23.81,
                             'milliliter(ml)': 2381}
    # tags
    RECIPE_TAGS = ['Italian', 'Chinese', 'American', 'French',
                   'Vegan', 'Soup', 'Spicy']
    # photo
    CLIENT_ID = '5b2af5db85fc9a1'
    CLIENT_SECRET = 'fadb6addc1f2d5f8e09e4bf7dc5780e5071b9de6'
    # search
    WHOOSHEE_DIR = os.path.join(basedir, 'search.db')
    WHOSHEE_MIN_STRING_LEN = 3
    WHOOSHEE_WRITER_TIMEOUT = 2
    WHOOSHEE_URL = '/search_results'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.COOKZILLA_MAIL_SENDER,
            toaddrs=[cls.COOKZILLA_ADMIN],
            subject=cls.COOKZILLA_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'unix': UnixConfig,

    'default': DevelopmentConfig
}
