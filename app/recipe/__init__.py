from flask import Blueprint

recipe = Blueprint('main', __name__)

from . import views

