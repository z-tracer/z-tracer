from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors, views_task, views_function, views_perf
#from ..record import Record