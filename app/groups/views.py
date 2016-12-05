from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from . import groups
from .forms import GroupForm
from .. import db
from ..models import Group, Role, User, Recipe, Review, GroupMember


@groups.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = GroupForm()
    if form.validate_on_submit():
        group = Group(creator=current_user,
                      title=form.title.data,
                      about_group=form.about_group.data)
        # add creator as member
        gm = GroupMember(member=current_user,
                         group=group)
        db.session.add(group)
        db.session.add(gm)
        db.session.commit()
        flash('You have created a group.')
        return redirect(url_for('groups.group_profile', id=group.id))
    return render_template('groups/create.html', form=form)


@groups.route('/<int:id>', methods=['GET', 'POST'])
def group_profile(id):
    group = Group.query.get_or_404(id)
    # form = ReviewForm()
    # if form.validate_on_submit():
    #     review = Review(body=form.body.data,
    #                     recipe=recipe,
    #                     author=current_user._get_current_object())
    #     db.session.add(review)
    #     flash('Your review has been published.')
    #     return redirect(url_for('.recipe', id=recipe.id, page=-1))
    # page = request.args.get('page', 1, type=int)
    # if page == -1:
    #     page = (recipe.reviews.count() - 1) // \
    #            current_app.config['COOKZILLA_COMMENTS_PER_PAGE'] + 1
    # pagination = recipe.reviews.order_by(Review.timestamp.asc()).paginate(
    #     page, per_page=current_app.config['COOKZILLA_COMMENTS_PER_PAGE'],
    #     error_out=False)
    # reviews = pagination.items
    return render_template('groups/group.html', group=group)


@groups.route('/<username>')
@login_required
def group_list(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.groups.paginate(
        page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
        error_out=False)
    groups = [{'user': item.member, 'group': item.group, 'member_since': item.member_since}
              for item in pagination.items]
    return render_template('groups/group_members.html', user=user,
                           endpoint='.groups', pagination=pagination,
                           groups=groups)
