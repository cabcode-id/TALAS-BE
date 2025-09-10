from flask import Blueprint

today_bp = Blueprint("today", __name__, url_prefix="/today")

from . import route
