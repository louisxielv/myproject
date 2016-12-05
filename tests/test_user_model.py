import time
import unittest
from datetime import datetime

from app import create_app, db
from app.models import User, AnonymousUser, Role, Permission, Follow, Group, Event, Report


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expired_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_invalid_reset_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_reset_token()
        self.assertFalse(u2.reset_password(token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))

    def test_valid_email_change_token(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('susan@example.org')
        self.assertTrue(u.change_email(token))
        self.assertTrue(u.email == 'susan@example.org')

    def test_invalid_email_change_token(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_email_change_token('david@example.net')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'susan@example.org')

    def test_duplicate_email_change_token(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u2.generate_email_change_token('john@example.com')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'susan@example.org')

    def test_roles_and_permissions(self):
        u = User(email='john@example.com', password='cat')
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))

    def test_timestamps(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertTrue(
            (datetime.utcnow() - u.joined_since).total_seconds() < 3)
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 3)

    def test_ping(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_gravatar(self):
        u = User(email='john@example.com', password='cat')
        with self.app.test_request_context('/'):
            gravatar = u.gravatar()
            gravatar_256 = u.gravatar(size=256)
            gravatar_pg = u.gravatar(rating='pg')
            gravatar_retro = u.gravatar(default='retro')
        with self.app.test_request_context('/', base_url='https://example.com'):
            gravatar_ssl = u.gravatar()
        self.assertTrue('http://www.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6' in gravatar)
        self.assertTrue('s=256' in gravatar_256)
        self.assertTrue('r=pg' in gravatar_pg)
        self.assertTrue('d=retro' in gravatar_retro)
        self.assertTrue('https://secure.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6' in gravatar_ssl)

    def test_follows(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        timestamp_before = datetime.utcnow()
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertTrue(u1.followed.count() == 2)
        self.assertTrue(u2.followers.count() == 2)
        f = u1.followed.all()[-1]
        self.assertTrue(f.followed == u2)
        self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
        f = u2.followers.all()[-1]
        self.assertTrue(f.follower == u1)
        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)
        u2.follow(u1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        db.session.delete(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)

    def test_groups(self):
        timestamp_before1 = datetime.utcnow()
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        g1 = Group(title='whatfood')
        g2 = Group(title='hayguys')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(g1)
        db.session.add(g2)
        db.session.commit()
        self.assertFalse(u1.is_member(g1))
        self.assertFalse(u1.is_member(g2))
        self.assertFalse(g1.is_member(u1))
        timestamp_before = datetime.utcnow()
        u1.member(g1)
        u1.member(g2)
        u2.member(g1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        self.assertTrue(u1.is_member(g1))
        self.assertTrue(u1.is_member(g2))
        self.assertTrue(g1.is_member(u1))
        self.assertTrue(u1.groups.count() == 2)
        self.assertTrue(g1.members.count() == 2)
        g = u1.groups.all()[-1]
        self.assertTrue(g.group == g2)
        self.assertTrue(timestamp_before <= g.member_since <= timestamp_after)
        u1.unmember(g2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.groups.count() == 1)
        self.assertTrue(g2.members.count() == 0)
        g = u1.groups.all()[-1]
        self.assertTrue(g.group == g1)

    def test_events(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        u3 = User(email='john@exaple.com', password='cat')
        u4 = User(email='suan@example.org', password='dog')

        g1 = Group(title='whatfood', creator=u1)
        g2 = Group(title='hayguys', creator=u2)

        db.session.add(g1)
        db.session.add(g2)

        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)

        self.assertFalse(u1.is_member(g1))
        self.assertFalse(u2.is_member(g1))
        self.assertFalse(u3.is_member(g1))
        self.assertFalse(u4.is_member(g1))

        u1.member(g1)
        u2.member(g1)
        u2.member(g2)
        u3.member(g1)
        u4.member(g1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        self.assertTrue(u1.is_member(g1))
        self.assertTrue(u2.is_member(g1))
        self.assertTrue(u3.is_member(g1))
        self.assertTrue(u4.is_member(g1))

        e1 = Event(title='a', group=g1, creator=u1, timestamp=datetime(2017, 1, 5, 14, 51, 54, 111111))
        e2 = Event(title='b', group=g1, creator=u2)
        db.session.add(e1)
        db.session.add(e2)

        self.assertTrue(e1.is_event_of_group(g1))
        self.assertTrue(e2.is_event_of_group(g1))
        self.assertTrue(e1.is_event_of_user(u1))
        self.assertFalse(e1.is_event_of_user(u2))
        self.assertTrue(e1 in u1.get_all_events())
        self.assertTrue(e2 in u1.get_all_events())
        self.assertTrue(e1 in u1.get_all_available_events())
        self.assertFalse(e2 in u1.get_all_available_events())
        self.assertTrue(e1 in g1.get_available_events())
        self.assertFalse(e2 in g1.get_available_events())
        self.assertFalse(u1.is_rsvp(e1))
        self.assertFalse(u2.is_rsvp(e1))
        self.assertFalse(u3.is_rsvp(e1))
        self.assertFalse(u4.is_rsvp(e1))

        u1.rsvp(e1)
        u2.unrsvp(e1)
        u3.rsvp(e1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        self.assertTrue(u1.is_rsvp(e1))
        self.assertTrue(u2.is_rsvp(e1))
        self.assertTrue(u3.is_rsvp(e1))
        self.assertFalse(u4.is_rsvp(e1))
        self.assertTrue(e1.is_rsvp(u1))
        self.assertFalse(e1.is_rsvp(u4))

        # self.assertTrue(e1 in u1.get_all_events())
        # self.assertFalse(e2 in u1.get_all_events())
        # datetime.datetime(2017, 1, 5, 14, 51, 54, 111111)

    def test_reports(self):
        e1 = Event(title='a')
        e2 = Event(title='b')
        r1 = Report(title='c', event=e1)
        r2 = Report(title='d', event=e1)
        db.session.add(r1)
        db.session.add(r2)
        db.session.add(e1)
        db.session.add(e2)
        self.assertTrue(r1 in e1.reports)
        self.assertTrue(r2 in e1.reports)
        self.assertFalse(r2 in e2.reports)

