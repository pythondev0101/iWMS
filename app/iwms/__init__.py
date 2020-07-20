from flask import Blueprint

bp_iwms = Blueprint('bp_iwms', __name__,template_folder='templates')


from . import routes
from . import models
