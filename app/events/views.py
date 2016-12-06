from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from . import events
from .forms import EventForm, ReportForm
from .. import db
from ..models import Group, Role, User, Recipe, Review, GroupMember, Event, Report, RSVP


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
        current_user.go(event)
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
    pagination = event.reports.order_by(Report.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_COMMENTS_PER_PAGE'],
        error_out=False)
    reports = pagination.items
    return render_template('events/event.html', event=event, form=form, reports=reports, pagination=pagination)


@events.route('/go/<int:id>')
@login_required
def go(id):
    event = Event.query.filter_by(id=id).first()
    if event is None:
        flash('Invalid event.')
        return redirect(url_for('.index'))
    if current_user.is_go(event):
        flash('You are going to this event.')
        return redirect(url_for('events.event_profile', id=id))
    current_user.go(event)
    flash('You have a new event: {}.'.format(event.title))
    return redirect(url_for('events.event_profile', id=id))


@events.route('/ungo/<int:id>')
@login_required
def ungo(id):
    event = Event.query.filter_by(id=id).first()
    if event is None:
        flash('Invalid event.')
        return redirect(url_for('.index'))
    if current_user.is_not_go(event):
        flash('You are not going to this event.')
        return redirect(url_for('events.event_profile', id=id))
    current_user.ungo(event)
    flash('You are not attending this event: {}'.format(event.title))
    return redirect(url_for('events.event_profile', id=id))


@events.route('/<username>')
@login_required
def event_list(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.events.order_by(RSVP.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_FOLLOWERS_PER_PAGE'],
        error_out=False)
    events = [{'user': item.member, 'event': item.event, 'timestamp': item.timestamp}
              for item in pagination.items]
    return render_template('events/my_events_list.html', user=user,
                           endpoint='.events', pagination=pagination,
                           events=events)
