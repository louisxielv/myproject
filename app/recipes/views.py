from flask import render_template, redirect, url_for, abort, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.recipes.forms import RecipeForm, PhotoForm
from app.utils import Imgur
from . import recipes
from .. import db
from ..main.forms import ReviewForm
from ..models import Permission, Recipe, Review, Ingredient, Tag
from ..utils.Imgur import Imgur

imgur_handler = Imgur()


@recipes.route('/upload/', methods=('GET', 'POST'))
def upload():
    form = PhotoForm()
    if form.validate_on_submit():
        filename = secure_filename(form.photo.data.filename)
        print(filename)
        # form.photo.data.save('uploads/' + filename)
        print(form.photo.data)
        image_data = imgur_handler.send_image(form.photo.data)
        print(image_data)
    else:
        filename = None
    return render_template('recipes/photo.html', form=form, filename=filename)


# @recipes.route("/image_upload", methods=["GET", "POST"])
# def get_img():
#     if request.method == "POST":
#         image = request.files.get("my_image")
#         image_data = imgur_handler.send_image(image)
#
#         print(image_data)
#         print(image_data["success"]) # True
#         print(image_data["data"]["height"]) # 200
#         print(image_data["data"]["link"]) # "http://imgur.com/SbBGk.jpg"
#         print(image_data["data"]["deletehash"]) # "eYZd3NNJHsbreD1"


@recipes.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    recipe_form = RecipeForm()
    photo_form = PhotoForm()

    print("haha")
    if request.method == 'POST':
        print(photo_form.photo.data)

    if current_user.can(Permission.WRITE_ARTICLES) and recipe_form.validate_on_submit() and photo_form.photo.data:
        # recipe
        title = recipe_form.title.data
        serving = recipe_form.serving.data
        body = recipe_form.body.data

        recipe = Recipe(author=current_user._get_current_object(), title=title, serving=serving, body=body)
        db.session.add(recipe)
        db.session.commit()

        # ingredient at least one
        name = recipe_form.name.data
        unit = recipe_form.unit.data
        quantity = recipe_form.quantity.data
        ingredient = Ingredient(name=name, recipe=recipe, unit=unit, quantity=quantity)
        db.session.add(ingredient)

        print(photo_form.photo.data)
        # if link is provided
        if recipe_form.links.data:
            tmp = recipe_form.links.data.split("/")
            other_link = Recipe.query.filter_by(id=int(tmp[-1])).first()
            if other_link:
                recipe.link(other_link)
                db.session.add(recipe)

        # if tags is provided
        if recipe_form.tags.data:
            tag = Tag.query.filter_by(id=int(recipe_form.tags.data[0])).first()
            if tag:
                recipe.tag(tag)
                db.session.add(recipe)

        db.session.commit()

        flash('You have posted your recipe', 'success')

        return redirect(url_for('.recipe', id=recipe.id))

    if recipe_form.errors:
        print(recipe_form.errors)
        flash('Something error')

    return render_template('recipes/create.html', recipe_form=recipe_form, photo_form=photo_form)


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
    return render_template('recipes/recipe_full.html', recipe=recipe, form=form,
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