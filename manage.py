#!/usr/bin/env python
import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage

    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from app import create_app, db
from app.models import User, Follow, Role, Permission, Recipe, Review, Group, GroupMember, Ingredient, Tag, Event, \
    Report, RSVP, LogEvent
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Recipe=Recipe, Review=Review,
                Group=Group, GroupMember=GroupMember, Ingredient=Ingredient,
                Tag=Tag, Event=Event, Report=Report, RSVP=RSVP,
                LogEvent=LogEvent)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade

    # migrate database to latest revision
    upgrade()

    db.drop_all()
    db.create_all()
    print("set up db")
    # create user roles
    Role.insert_roles()
    Tag.insert_tags()
    print("insert all")
    # fake
    u1 = User(email='nychent@gmail.com', username='chet', password='chet', confirmed=True)
    u2 = User(email='louisxielv@gmail.com', username='louisxielv', password='123', confirmed=True)
    u3 = User(email='no@name.com', username='noname', password='noname', confirmed=True)
    db.session.add(u1)
    db.session.add(u2)
    db.session.add(u3)
    db.session.commit()
    User.generate_fake()
    print("user good")

    Recipe.generate_fake()
    Ingredient.generate_fake()
    Tag.generate_fake()
    print("recipe good")
    Review.generate_fake()
    print("review good")

    # create self-follows for all users
    User.add_self_follows()
    print("self follow")

    # group
    Group.generate_fake()
    print("group ready")

    Event.generate_fake()
    print("event ready")

    Report.generate_fake()
    print("report ready")


if __name__ == '__main__':
    manager.run()
