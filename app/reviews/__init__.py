from flask import Blueprint

reviews = Blueprint('reviews', __name__)

from . import views
