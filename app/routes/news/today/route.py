from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from app import db
from app.model import Title, Article
from sqlalchemy import func, case,  desc

from . import today_bp

@today_bp.route("/source", methods=["GET"])
def get_today_source_counts():
    try:
        # Query untuk menghitung jumlah artikel per sumber hanya untuk hari ini
        source_counts = (
            db.session.query(
                Article.source,
                db.func.count(Article.id).label("count")
            )
            .filter(db.func.date(Article.date) == date.today())
            .group_by(Article.source)
            .all()
        )
        
        # Ubah hasil query menjadi list of dict
        result = [
            {"source": source, "count": count}
            for source, count in source_counts
        ]
        
        return jsonify({
            "success": True,
            "data": result,
            "count": len(result)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@today_bp.route("/title", methods=["GET"])
def get_today_titles():
    try:
        # Ambil semua data Title untuk hari ini
        today_titles = Title.query.filter(db.func.date(Title.date) == date.today()).all()
        
        # Konversi hasil query ke dict
        result = [t.to_dict() if hasattr(t, "to_dict") else {
            "title_index": t.title_index,
            "title": t.title,
            "image": t.image,
            "all_summary": t.all_summary,
            "date": t.date,
            "cluster": t.cluster,
            "analysis": t.analysis
        } for t in today_titles]
        
        return jsonify({
            "success": True,
            "data": result,
            "count": len(result)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@today_bp.route("/groups", methods=["GET"])
def get_title_groups():
    try:
        # Ambil semua title_index untuk hari ini
        today_titles = Title.query.with_entities(Title.title_index).filter(
            db.func.date(Title.date) == date.today()
        ).all()
        
        title_groups = {}
        for (title_index,) in today_titles:
            # Ambil semua artikel yang punya title_index sama
            articles = (
                Article.query.with_entities(
                    Article.id, 
                    Article.title, 
                    Article.source
                )
                .filter(Article.title_index == title_index)
                .all()
            )
            title_groups[title_index] = [
                {"id": a.id, "title": a.title, "source": a.source}
                for a in articles
            ]
        
        return jsonify({
            "success": True,
            "data": title_groups,
            "count": len(title_groups)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    

