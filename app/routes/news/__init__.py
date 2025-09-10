from flask import Blueprint

news_bp = Blueprint("news", __name__, url_prefix="/news")

from . import route             
from .today import today_bp       


news_bp.register_blueprint(today_bp)
