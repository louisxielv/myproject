from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime
from . import groups
from .forms import GroupForm
from .. import db
from ..models import Group, Role, User, Recipe, Review, GroupMember, Event


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
@login_required
def group_profile(id):
    group = Group.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = group.events.order_by(Event.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_POSTS_PER_PAGE'],
        error_out=False)
    events = pagination.items
    return render_template('groups/group.html', group=group, events=events, pagination=pagination)


@groups.route('/<username>')
@login_required
def group_list(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.groups.order_by(GroupMember.member_since.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
        error_out=False)
    groups = [{'user': item.member, 'group': item.group, 'member_since': item.member_since}
              for item in pagination.items]
    return render_template('groups/my_groups_list.html', user=user,
                           endpoint='.groups', pagination=pagination,
                           groups=groups)


@groups.route('/member/<int:id>')
@login_required
def member(id):
    group = Group.query.filter_by(id=id).first()
    if group is None:
        flash('Invalid group.')
        return redirect(url_for('.index'))
    if current_user.is_member(group):
        flash('You are already a member of this group.')
        return redirect(url_for('groups.group_profile', id=id))
    current_user.member(group)
    flash('You are now a member of {}.'.format(group.title))
    return redirect(url_for('groups.group_profile', id=id))


@groups.route('/unmember/<int:id>')
@login_required
def unmember(id):
    group = Group.query.filter_by(id=id).first()
    if group is None:
        flash('Invalid group.')
        return redirect(url_for('.index'))
    if not current_user.is_member(group):
        flash('You are not a member of this group.')
        return redirect(url_for('groups.group_profile', id=id))
    current_user.unmember(group)
    flash('You are not a member of {} anymore.'.format(group.title))
    return redirect(url_for('groups.group_profile', id=id))
