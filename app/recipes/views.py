from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import recipes
from app.recipes.forms import RecipeForm, IngredientsForm
from ..main.forms import ReviewForm
from .. import db
from ..models import Permission, Role, User, Recipe, Review, Ingredient


from ..decorators import admin_required, permission_required


@recipes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    recipe_form = RecipeForm()
    ingredient_form = IngredientsForm()

    if current_user.can(Permission.WRITE_ARTICLES) \
            and recipe_form.validate_on_submit() \
            and ingredient_form.validate_on_submit():
        # recipe
        title = recipe_form.title.data
        serving = recipe_form.serving.data
        body = recipe_form.body.data

        recipe = Recipe(author=current_user._get_current_object(), title=title, serving=serving, body=body)
        db.session.add(recipe)
        db.session.commit()

        # ingredient
        name = ingredient_form.name.data
        unit = ingredient_form.unit.data
        quantity = ingredient_form.quantity.data
        ingredient = Ingredient(name=name, recipe=recipe, unit=unit, quantity=quantity)
        db.session.add(recipe)
        db.session.commit()

        flash('You have posted your recipe', 'success')

        return redirect(url_for('.recipe', id=recipe.id))

    if recipe_form.errors:
        flash('Something error', 'danger')

    return render_template('recipes/create.html', recipe_form=recipe_form, ingredient_form=ingredient_form)


@recipes.route('/<int:id>', methods=['GET', 'POST'])
def recipe(id):
    recipe = Recipe.query.get_or_404(id)
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(body=form.body.data,
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
    return render_template('recipes/recipe.html', recipes=[recipe], form=form,
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