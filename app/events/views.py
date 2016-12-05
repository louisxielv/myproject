from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from . import events
from .forms import EventForm, ReportForm
from .. import db
from ..models import Group, Role, User, Recipe, Review, GroupMember, Event, Report


@events.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    group_id = request.args.get('group_id')
    group = Group.query.get_or_404(group_id)
    form = EventForm()
    if form.validate_on_submit():
        event = Event(group=group,
                      creator=current_user,
                      title=form.title.data,
                      timestamp=form.timestamp.data,
                      location=form.location.data,
                      about_event=form.about_event.data)
        # add creator as member
        current_user.rsvp(event)
        db.session.add(current_user)
        db.session.add(event)
        db.session.commit()
        flash('You have created a event.')
        return redirect(url_for('events.event_profile', id=event.id))

    if form.errors:
        tmp = [str(k)+" "+str(v[0]) for k, v in form.errors.items()]
        flash("\n".join(tmp))

    return render_template('events/create.html', form=form)


@events.route('/<int:id>', methods=['GET', 'POST'])
@login_required
def event_profile(id):
    event = Event.query.get_or_404(id)
    group = event.group
    if not current_user.is_member(group):
        flash("You cannot see this event because you are not member")
        return redirect(url_for('groups.group_profile', id=group.id))

    form = ReportForm()
    if form.validate_on_submit():
        report = Report(event=event,
                        author=current_user._get_current_object(),
                        title=form.title.data,
                        body=form.body.data)
        db.session.add(report)
        flash('Your report has been published.')
        return redirect(url_for('events.event_profile', id=event.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (event.reports.count() - 1) // \
               current_app.config['COOKZILLA_COMMENTS_PER_PAGE'] + 1
    pagination = event.reports.order_by(Report.timestamp.asc()).paginate(
        page, per_page=current_app.config['COOKZILLA_COMMENTS_PER_PAGE'],
        error_out=False)
    reports = pagination.items
    return render_template('events/event.html', event=event, form=form, reports=reports, pagination=pagination)


# @groups.route('/<username>')
# @login_required
# def group_list(username):
#     user = User.query.filter_by(username=username).first()
#     if user is None:
#         flash('Invalid user.')
#         return redirect(url_for('.index'))
#     page = request.args.get('page', 1, type=int)
#     pagination = user.groups.paginate(
#         page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
#         error_out=False)
#     groups = [{'user': item.member, 'group': item.group, 'member_since': item.member_since}
#               for item in pagination.items]
#     return render_template('groups/group_members.html', user=user,
#                            endpoint='.groups', pagination=pagination,
#                            groups=groups)
#

