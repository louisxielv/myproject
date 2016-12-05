from flask import render_template, redirect, url_for, abort, flash, request, current_app
from flask_login import login_required, current_user

from app.recipes.forms import RecipeForm, ReviewForm
from . import recipes
from .. import db
from ..models import Permission, Recipe, Review, Ingredient, Tag
from ..utils.Imgur import Imgur
from ..utils.tools import gen_rnd_filename
from werkzeug.utils import secure_filename

imgur_handler = Imgur()

import os
import datetime
import random


@recipes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    recipe_form = RecipeForm()

    if current_user.can(Permission.WRITE_ARTICLES) and recipe_form.validate_on_submit():
        # recipe
        title = recipe_form.title.data
        serving = recipe_form.serving.data
        body = recipe_form.body.data
        # photo
        filename = secure_filename(recipe_form.photo.data.filename)
        filename = gen_rnd_filename(filename)
        fpath = os.path.join(current_app.static_folder, 'upload', filename)
        recipe_form.photo.data.save(os.path.join(fpath))
        photos = url_for('static', filename='{}/{}'.format('upload', filename))

        recipe = Recipe(author=current_user._get_current_object(),
                        title=title, serving=serving, body=body, photos=photos)
        db.session.add(recipe)
        db.session.commit()

        # Snoopyimage.jpg
        # [{'name': 'app', 'unit': 'pound(lb)', 'quantity': '1'}]
        # [{'name': 'ban', 'unit': 'pound(lb)', 'quantity': '2'}, {'name': '', 'unit': 'pound(lb)', 'quantity': ''},
        #  {'name': '', 'unit': 'pound(lb)', 'quantity': ''}, {'name': '', 'unit': 'pound(lb)', 'quantity': ''}]
        # ['2', '3', '4']
        # [{'link': 'http://127.0.0.1:5000/recipes/1'}, {'link': 'http://127.0.0.1:5000/recipes/2'}]

        # ingredient must one
        tmp = recipe_form.ingredients.data[0]
        name = tmp["name"]
        unit = tmp["unit"]
        try:
            quantity = int(tmp["quantity"])
            ingredient = Ingredient(name=name, recipe=recipe, unit=unit, quantity=quantity)
            db.session.add(ingredient)
        except:
            pass

        # ingredient optical
        for ingredient in recipe_form.ingredients_optical.data:
            if ingredient["name"] and ingredient["quantity"]:
                name = ingredient["name"]
                unit = ingredient["unit"]
                try:
                    quantity = int(ingredient["quantity"])
                    ingredient = Ingredient(name=name, recipe=recipe, unit=unit, quantity=quantity)
                    db.session.add(ingredient)
                except:
                    pass

        # if link is provided
        for data in recipe_form.links.data:
            try:
                tmp = data["link"].split("/")
                other_link = Recipe.query.filter_by(id=int(tmp[-1])).first()
                if other_link:
                    recipe.link(other_link)
                    db.session.add(recipe)
            except:
                pass

        # if tags is provided
        for tag in recipe_form.tags.data:
            try:
                tag = Tag.query.filter_by(id=int(tag)).first()
                if tag:
                    recipe.tag(tag)
                    db.session.add(recipe)
            except:
                pass

        db.session.commit()

        flash('You have posted your recipe')

        return redirect(url_for('.recipe', id=recipe.id))

    if recipe_form.errors:
        tmp = [str(k)+" "+str(v[0]) for k, v in recipe_form.errors.items()]
        flash("\n".join(tmp))

    return render_template('recipes/create.html', recipe_form=recipe_form)


@recipes.route('/<int:id>', methods=['GET', 'POST'])
def recipe(id):
    recipe = Recipe.query.get_or_404(id)
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(title=form.title.data,
                        body=form.body.data,
                        rating=form.rating.data,
                        suggestion=form.suggestion.data,
                        recipe=recipe,
                        author=current_user._get_current_object())
        db.session.add(review)
        flash('Your review has been published.')
        return redirect(url_for('.recipe', id=recipe.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (recipe.reviews.count() - 1) // \
               current_app.config['COOKZILLA_COMMENTS_PER_PAGE'] + 1
    pagination = recipe.reviews.order_by(Review.timestamp.asc()).paginate(
        page, per_page=current_app.config['COOKZILLA_COMMENTS_PER_PAGE'],
        error_out=False)
    reviews = pagination.items
    return render_template('recipes/recipe.html', recipe=recipe, form=form,
                           reviews=reviews, pagination=pagination)


@recipes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    recipe = Recipe.query.get_or_404(id)
    if current_user != recipe.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = RecipeForm()
    if form.validate_on_submit():
        recipe.body = form.body.data
        db.session.add(recipe)
        flash('The recipe has been updated.')
        return redirect(url_for('.recipe', id=recipe.id))
    form.body.data = recipe.body
    return render_template('recipes/edit_recipe.html', form=form)
