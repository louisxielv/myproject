import hashlib
from datetime import datetime

from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager

# 128 is for avatar
LENGTH = 64


# user part
class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(LENGTH), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role {!r}, Name: {!r}>'.format(self.id, self.name)


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# many to many relationship
# group_member = db.Table('group_member',
#                         db.Column('user.id', db.INTEGER, db.ForeignKey('users.id')),
#                         db.Column('group_id', db.INTEGER, db.ForeignKey('groups.id')),
#                         db.Column('member_since', db.DATETIME, default=datetime.utcnow))

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    member_id = db.Column(db.INTEGER, db.ForeignKey('users.id'), primary_key=True)
    group_id = db.Column(db.INTEGER, db.ForeignKey('groups.id'), primary_key=True)
    member_since = db.Column(db.DATETIME, default=datetime.utcnow)
    admin = db.Column(db.BOOLEAN, default=False)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(LENGTH), unique=True, index=True)
    username = db.Column(db.String(LENGTH), unique=True, index=True)
    name = db.Column(db.String(LENGTH))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(LENGTH * 2))
    confirmed = db.Column(db.Boolean, default=False)
    about_me = db.Column(db.Text())
    joined_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))  # https://en.gravatar.com/
    recipes = db.relationship('Recipe', backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='author', lazy='dynamic')

    groups = db.relationship('GroupMember',
                             backref=db.backref('member', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')

    # groups = db.relationship('Group',   # table name
    #                          secondary='group_member',  # association table
    #                          backref=db.backref('members', lazy='dynamic'),  # User.groups and Group.members
    #                          lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     joined_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
        db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email in current_app.config['COOKZILLA_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        self.followed.append(Follow(followed=self))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    # follow part
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    @property
    def followed_recipes(self):
        return Recipe.query.join(Follow,
                                 Follow.followed_id == Recipe.author_id).filter(Follow.follower_id == self.id)

    # membership part
    def member(self, group):
        if not self.is_member(group):
            gm = GroupMember(member=self, group=group)
            db.session.add(gm)

    def unmember(self, group):
        gm = self.groups.filter_by(group_id=group.id).first()
        if gm:
            db.session.delete(gm)

    def is_member(self, group):
        return self.groups.filter_by(group_id=group.id).first() is not None

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return '<id: {!r}, User {!r}, email: {!r}>\n' \
            .format(self.id,
                    self.username,
                    self.email)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# recipe part

# many to many relationship
relates = db.Table('relates',
                   db.Column('link_id', db.INTEGER, db.ForeignKey('recipes.id')),
                   db.Column('linked_id', db.INTEGER, db.ForeignKey('recipes.id')))

recipe_tags = db.Table('recipe_tags',
                       db.Column('recipe_id', db.INTEGER, db.ForeignKey('recipes.id')),
                       db.Column('tag_id', db.INTEGER, db.ForeignKey('tags.id')))


class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    photos = db.Column(db.String(LENGTH * 2), default="")
    title = db.Column(db.String(LENGTH))
    serving = db.Column(db.INTEGER, default=1)  # less than 10
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    ingredients = db.relationship('Ingredient', backref='recipe', lazy='dynamic')  # Ingredient.recipe
    reviews = db.relationship('Review', backref='recipe', lazy='dynamic')
    links = db.relationship('Recipe',  # table name
                            secondary=relates,  # association table
                            primaryjoin=(relates.c.link_id == id),
                            secondaryjoin=(relates.c.linked_id == id),
                            backref=db.backref('linkeds', lazy='dynamic'),  # Recipe.links
                            lazy='dynamic')
    tags = db.relationship('Tag',
                           secondary='recipe_tags',
                           backref=db.backref('recipes', lazy='dynamic'),  # Recipe.tags and Tag.recipes
                           lazy='dynamic')

    @staticmethod
    def generate_fake(count=500):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Recipe(photos=u.gravatar(size=200),
                       title=forgery_py.lorem_ipsum.sentences(randint(1, 2)),
                       serving=randint(1, 5),
                       body=forgery_py.lorem_ipsum.sentences(randint(1, 10)),
                       timestamp=forgery_py.date.date(True),
                       author=u)
            db.session.add(p)
        db.session.commit()

    # link part
    def link(self, link):
        if not self.is_link(link):
            self.links.append(link)
            db.session.add(self)

    def unlink(self, link):
        if self.is_link(link):
            self.links.remove(link)
            db.session.add(self)

    def is_link(self, link):
        return link in self.links

    # tag part
    def tag(self, tag):
        if not self.is_tag(tag):
            self.tags.append(tag)
            db.session.add(self)

    def untag(self, tag):
        if self.is_tag(tag):
            self.tags.remove(tag)
            db.session.add(self)

    def is_tag(self, tag):
        return tag in self.tags


# one to many
class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    name = db.Column(db.String(LENGTH), primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), primary_key=True)
    unit = db.Column(db.String(LENGTH))
    quantity = db.Column(db.INTEGER)

    @staticmethod
    def generate_fake(count=1000):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, choice
        import forgery_py

        seed()
        recipe_count = Recipe.query.count()
        icc = list(current_app.config["INGREDIENT_CONVERSION"].keys())
        for _ in range(count):
            r = Recipe.query.offset(randint(0, recipe_count - 1)).first()
            i = Ingredient(name=forgery_py.lorem_ipsum.word(),
                           unit=choice(icc),
                           quantity=randint(0, 1000) + 1,
                           recipe=r)
            db.session.add(i)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(LENGTH))

    @staticmethod
    def insert_tags():
        for t in current_app.config['RECIPE_TAGS']:
            tag = Tag.query.filter_by(tag=t).first()
            if tag is None:
                tag = Tag(tag=t)
                db.session.add(tag)
        db.session.commit()

    @staticmethod
    def generate_fake(count=1000):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint

        seed()
        recipe_count = Recipe.query.count()
        tag_count = Tag.query.count()
        for _ in range(count):
            r = Recipe.query.offset(randint(0, recipe_count - 1)).first()
            t = Tag.query.offset(randint(0, tag_count - 1)).first()
            r.tag(t)
            db.session.add(r)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


# review part
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)
    rating = db.Column(db.INTEGER, default=5)
    suggestion = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))

    @staticmethod
    def generate_fake(count=1000):
        from random import seed, randint
        from sqlalchemy.exc import IntegrityError
        import forgery_py

        seed()
        user_count = User.query.count()
        recipe_count = Recipe.query.count()
        for _ in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            rp = Recipe.query.offset(randint(0, recipe_count - 1)).first()
            rv = Review(title=forgery_py.lorem_ipsum.sentences(randint(1, 2)),
                        body=forgery_py.lorem_ipsum.sentences(randint(1, 10)),
                        rating=randint(0, 4) + 1,
                        suggestion=forgery_py.lorem_ipsum.sentences(randint(1, 2)),
                        timestamp=forgery_py.date.date(True),
                        author=u,
                        recipe=rp)
            db.session.add(rv)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


# group part

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, index=True, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(LENGTH))
    about_group = db.Column(db.Text)
    grouped_since = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    members = db.relationship('GroupMember',
                              backref=db.backref('group', lazy='joined'),
                              lazy='dynamic',
                              cascade='all, delete-orphan')
    events =

    def __repr__(self):
        return '<id {!r}, title: {!r}>\n'.format(self.id, self.title)

    # membership part
    def is_member(self, user):
        return self.members.filter_by(member_id=user.id).first() is not None


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.INTEGER, index=True, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(LENGTH))
    timestamp = db.Column(db.DATETIME, default=datetime.utcnow)
    location = db.Column(db.String(LENGTH))
    about_event = db.Column(db.TEXT)
    rsvp =
    reports =


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.INTEGER, index=True, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(LENGTH))
    timestamp = db.Column(db.DATETIME, default=datetime.utcnow)
    body = db.Column(db.TEXT)