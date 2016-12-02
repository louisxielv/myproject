from flask import Blueprint

recipes = Blueprint('recipes', __name__)

from . import views

from ..models import Permission


@recipes.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
