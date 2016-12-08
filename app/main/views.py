from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from sqlalchemy import func

from . import main
from .forms import EditProfileForm, EditProfileAdminForm, SearchForm
from .. import db
from ..decorators import admin_required, permission_required
from ..models import Permission, Role, User, Recipe, Tag, Follow, LogEvent


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['COOKZILLA_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query1 = current_user.query_logs
        query2 = current_user.followed_recipes
        if query1:
            query = query1.union(query2)
            query = query.group_by(Recipe).add_columns(func.sum(LogEvent.ct).label("ct"))
            query = query.order_by(LogEvent.ct.desc()).order_by(Recipe.timestamp.desc())
        else:
            query = query2
        query = query.with_entities(Recipe)
    else:
        query = Recipe.query.order_by(Recipe.timestamp.desc())

    pagination = query.paginate(
        page, per_page=current_app.config['COOKZILLA_POSTS_PER_PAGE'],
        error_out=False)
    recipes = pagination.items
    tags = Tag.query.all()
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('main.search_results', query=form.search.data))
    return render_template('index.html', form=form, recipes=recipes,
                           show_followed=show_followed, pagination=pagination, tags=tags)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.recipes.order_by(Recipe.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_POSTS_PER_PAGE'],
        error_out=False)
    recipes = pagination.items

    follows = user.followers.filter(Follow.follower_id != user.id).order_by(Follow.timestamp.desc()).limit(
        current_app.config["COOKZILLA_FOLLOWERS_PER_PAGE"]).all()
    followers = [{'user': item.follower, 'timestamp': item.timestamp}
                 for item in follows]

    follows = user.followed.filter(Follow.followed_id != user.id).order_by(Follow.timestamp.desc()).limit(
        current_app.config["COOKZILLA_FOLLOWERS_PER_PAGE"]).all()
    followeds = [{'user': item.followed, 'timestamp': item.timestamp}
                 for item in follows]

    return render_template('users/user.html', user=user, recipes=recipes,
                           followers=followers, followeds=followeds,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.about_me.data = current_user.about_me
    return render_template('users/edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.about_me.data = user.about_me
    return render_template('users/edit_profile.html', form=form, user=user)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.filter(Follow.follower_id != user.id).order_by(Follow.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('users/followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.filter(Follow.followed_id != user.id).order_by(Follow.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('users/followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/search_results/<query>')
def search_results(query):
    import time
    from sqlalchemy import or_
    start = time.time()
    recipes = Recipe.query.order_by(Recipe.timestamp.desc()) \
        .filter(or_(Recipe.title.contains(query), Recipe.body.contains(query))) \
        .limit(current_app.config["SEARCH_RESULTS"]).all()
    end = time.time()
    time = "{:.8f} seconds".format(end - start)
    # log
    for r in recipes:
        LogEvent.log(current_user, query, r)
    return render_template('utils/search_results.html',
                           query=query,
                           recipes=recipes,
                           time=time)


@main.route('/logs')
@admin_required
def log():
    page = request.args.get('page', 1, type=int)
    pagination = LogEvent.query.order_by(LogEvent.logged_at.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
        error_out=False)
    logs = [{'user': item.user, "op": item.op, 'recipe': item.recipe, "ct": item.ct, 'logged_at': item.logged_at}
            for item in pagination.items]
    return render_template('logs/logs.html', endpoint='main.log', pagination=pagination,
                           logs=logs)


