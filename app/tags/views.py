from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user

from . import tags
from .. import db
from ..models import Tag, Recipe


@tags.route('/<int:id>', methods=['GET', 'POST'])
def tag(id):
    tag = Tag.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = tag.recipes.order_by(Recipe.timestamp.asc()).paginate(
        page, per_page=current_app.config['COOKZILLA_COMMENTS_PER_PAGE'],
        error_out=False)
    recipes = pagination.items
    return render_template('tags/tag.html', recipes=recipes, pagination=pagination)
