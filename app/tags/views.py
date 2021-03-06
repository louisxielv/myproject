from flask import render_template, request, current_app
from flask_login import current_user

from . import tags
from ..models import Tag, Recipe, LogEvent


@tags.route('/<int:id>', methods=['GET', 'POST'])
def tag(id):
    tag = Tag.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = tag.recipes.order_by(Recipe.timestamp.desc()).paginate(
        page, per_page=current_app.config['COOKZILLA_COMMENTS_PER_PAGE'],
        error_out=False)
    recipes = pagination.items
    tags = Tag.query.all()
    # log
    for r in recipes:
        LogEvent.log(current_user, tag.tag, r)
    return render_template('tags/tag.html', recipes=recipes, pagination=pagination, tags=tags)
