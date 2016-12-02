from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, ReviewForm, SearchForm
from app.recipes.forms import RecipeForm
from .. import db
from ..models import Permission, Role, User, Recipe, Review

from ..decorators import admin_required, permission_required


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
        query = current_user.followed_recipes
    else:
        query = Recipe.query
    pagination = query.order_by(Recipe.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_POSTS_PER_PAGE'],
        error_out=False)
    recipes = pagination.items
    return render_template('index.html', recipes=recipes,
                           show_followed=show_followed, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.recipes.order_by(Recipe.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_POSTS_PER_PAGE'],
        error_out=False)
    recipes = pagination.items
    return render_template('user.html', user=user, recipes=recipes,
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
    return render_template('edit_profile.html', form=form)


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
    return render_template('edit_profile.html', form=form, user=user)


# @main.route('/recipe/<int:id>', methods=['GET', 'POST'])
# def recipe(id):
#     recipe = Recipe.query.get_or_404(id)
#     form = ReviewForm()
#     if form.validate_on_submit():
#         review = Review(body=form.body.data,
#                         recipe=recipe,
#                         author=current_user._get_current_object())
#         db.session.add(review)
#         flash('Your review has been published.')
#         return redirect(url_for('.recipe', id=recipe.id, page=-1))
#     page = request.args.get('page', 1, type=int)
#     if page == -1:
#         page = (recipe.reviews.count() - 1) // \
#                current_app.config['COOKZILLA_COMMENTS_PER_PAGE'] + 1
#     pagination = recipe.reviews.order_by(Review.timestamp.asc()).paginate(
#         page, per_page=current_app.config['COOKZILLA_COMMENTS_PER_PAGE'],
#         error_out=False)
#     reviews = pagination.items
#     return render_template('recipe.html', recipes=[recipe], form=form,
#                            reviews=reviews, pagination=pagination)


# @main.route('/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit(id):
#     recipe = Recipe.query.get_or_404(id)
#     if current_user != recipe.author and not current_user.can(Permission.ADMINISTER):
#         abort(403)
#     form = RecipeForm()
#     if form.validate_on_submit():
#         recipe.body = form.body.data
#         db.session.add(recipe)
#         flash('The recipe has been updated.')
#         return redirect(url_for('.recipe', id=recipe.id))
#     form.body.data = recipe.body
#     return render_template('edit_recipe.html', form=form)


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
    pagination = user.followers.paginate(
        page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Review.query.order_by(Review.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_COMMENTS_PER_PAGE'],
        error_out=False)
    reviews = pagination.items
    return render_template('moderate.html', reviews=reviews,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    review = Review.query.get_or_404(id)
    review.disabled = False
    db.session.add(review)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    review = Review.query.get_or_404(id)
    review.disabled = True
    db.session.add(review)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/search', methods=['POST'])
@login_required
def search():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(url_for('search_results', query=form.search.data))
    return redirect(url_for('index'))


@main.route('/search_results/<query>')
@login_required
def search_results(query):
    recipes = Recipe.query.whoosh_search(query, current_app.config['MAX_SEARCH_RESULTS']).all()
    return render_template('search_results.html',
                           query=query,
                           recipes=recipes)
