from loguru import logger
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config


db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app, resources={
        r"/*": {"origins": '*'}
    })

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    logger.add("logs/app.log", rotation="1 week", retention="1 month", level="INFO")

    @app.before_request
    def log_request():
        logger.info(f"{request.method} {request.path}")

    @app.after_request
    def log_response(response):
        logger.info(f"Status: {response.status}")
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception(f"Unhandled error: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


    # --- Register blueprints ---
    from app.routes.cluster.route import cluster_bp
    from app.routes.bias.route import bias_bp
    from app.routes.hoax.route import hoax_bp
    from app.routes.ideology.route import ideology_bp
    from app.routes.embedding.route import embedding_bp
    from app.routes.title.route import title_bp
    from app.routes.summary.route import summary_bp
    from app.routes.analyze.route import analyze_bp
    from app.routes.cleaned.route import cleaned_bp
    from app.routes.separate.route import separate_bp
    from app.routes.process.route import process_bp
    from app.routes.antipode.route import antipode_bp
    from app.routes.ner.route import ner_bp
    from app.routes.crawler.route import crawler_bp
    from app.routes.news.route import news_bp
    
    app.register_blueprint(cluster_bp, url_prefix="/cluster")
    app.register_blueprint(bias_bp, url_prefix="/bias")
    app.register_blueprint(hoax_bp, url_prefix="/hoax")
    app.register_blueprint(ideology_bp, url_prefix="/ideology")
    app.register_blueprint(embedding_bp, url_prefix="/embedding")
    app.register_blueprint(title_bp, url_prefix="/title")
    app.register_blueprint(summary_bp, url_prefix="/summary")
    app.register_blueprint(analyze_bp, url_prefix="/analyze")
    app.register_blueprint(cleaned_bp, url_prefix="/cleaned")
    app.register_blueprint(separate_bp, url_prefix="/separate")
    app.register_blueprint(process_bp, url_prefix="/process-all")
    app.register_blueprint(antipode_bp, url_prefix="/antipode")
    app.register_blueprint(ner_bp, url_prefix="/ner")
    app.register_blueprint(crawler_bp, url_prefix="/crawlers")
    app.register_blueprint(news_bp, url_prefix="/news")

    return app
