from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from app import db
from app.model import Title, Article
from sqlalchemy import func, case,  desc
from . import news_bp

@news_bp.route("/", methods=["GET"])
def get_news():
    try:
        # Ambil title dari 1 hari terakhir
        news_items = (
            db.session.query(Title)
            .filter(Title.date >= date.today() - timedelta(days=1))
            .order_by(Title.date.desc())
            .all()
        )

        if not news_items:
            return jsonify({"success": True, "data": [], "total": 0})

        title_indices = [item.title_index for item in news_items]

        # Hitung liberal, conservative, neutral untuk setiap title_index
        counts_rows = (
            db.session.query(
                Article.title_index,
                func.sum(case((Article.ideology <= 0.25, 1), else_=0)).label("liberal"),
                func.sum(case((Article.ideology >= 0.75, 1), else_=0)).label("conservative"),
                func.sum(case(
                    ((Article.ideology > 0.25) & (Article.ideology < 0.75), 1), 
                    else_=0
                )).label("neutral")
            )
            .filter(Article.title_index.in_(title_indices))
            .group_by(Article.title_index)
            .all()
        )

        # Mapping hasil hitung ke dict
        counts_map = {
            row.title_index: {
                "liberal": int(row.liberal),
                "conservative": int(row.conservative),
                "neutral": int(row.neutral)
            }
            for row in counts_rows
        }

        # Bentuk hasil akhir
        result = []
        for item in news_items:
            counts = counts_map.get(item.title_index, {
                "liberal": 0,
                "conservative": 0,
                "neutral": 0
            })

            result.append({
                "title": item.title,
                "image": item.image,
                "all_summary": item.all_summary,
                "date": item.date,
                "title_index": item.title_index,
                "cluster": item.cluster,
                "counts": counts
            })

        return jsonify({
            "success": True,
            "data": result,
            "total": len(result)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@news_bp.route("/detail", methods=["GET"])
def get_news_detail():
    try:
        # Ambil title_index dari query string
        title_index = request.args.get("title_index", type=int)
        if not title_index:
            return jsonify({"success": False, "error": "No title_index provided"}), 400

        # OPTIMASI: Ambil data Title dengan kolom yang diperlukan saja
        news = (
            db.session.query(
                Title.title,
                Title.cluster,
                Title.image,
                Title.date,
                Title.all_summary,
                Title.analysis
            )
            .filter(Title.title_index == title_index)
            .first()
        )

        if not news:
            return jsonify({"success": False, "error": "Article not found"}), 404

        # OPTIMASI: Ambil articles dengan kolom yang diperlukan saja (tanpa content & embedding yang besar)
        articles = (
            db.session.query(
                Article.title,
                Article.url,
                Article.source,
                Article.date,
                Article.bias,
                Article.hoax,
                Article.ideology
            )
            .filter(Article.title_index == title_index)
            .all()
        )

        # OPTIMASI: Hitung ideology counts langsung saat iterasi (menghindari query tambahan)
        liberal_count = 0
        conservative_count = 0
        neutral_count = 0
        
        article_list = []
        for article in articles:
            # Parse ideology untuk counting
            try:
                ideology_val = float(article.ideology) if article.ideology else 0.5
            except (ValueError, TypeError):
                ideology_val = 0.5
            
            if ideology_val <= 0.25:
                liberal_count += 1
            elif ideology_val >= 0.75:
                conservative_count += 1
            else:
                neutral_count += 1
            
            article_list.append({
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "date": article.date,
                "bias": article.bias,
                "hoax": article.hoax,
                "ideology": article.ideology,
            })

        # Bentuk response dengan ideology counts
        return jsonify({
            "success": True,
            "title": news.title,
            "cluster": news.cluster,
            "image": news.image,
            "date": news.date,
            "all_summary": news.all_summary,
            "analysis": news.analysis,
            "articles": article_list,
            "counts": {
                "liberal": liberal_count,
                "conservative": conservative_count,
                "neutral": neutral_count
            },
            "total_articles": len(article_list)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@news_bp.route("/today", methods=["GET"])
def get_today_articles():
    try:
        verbose = request.args.get('verbose', 'False').lower() == 'true'
        
        # Query dasar untuk artikel dengan tanggal hari ini
        base_query = db.session.query(Article).filter(db.func.date(Article.date) == date.today())
        
        # Ambil data sesuai verbose
        if verbose:
            articles = base_query.all()
            result = [
                {
                    c.name: getattr(article, c.name)
                    for c in article.__table__.columns
                }
                for article in articles
            ]
        else:
            articles = base_query.all()
            result = [
                {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "image": article.image,
                    "date": article.date,
                    "bias": article.bias,
                    "hoax": article.hoax,
                    "ideology": article.ideology,
                    "title_index": article.title_index,
                }
                for article in articles
            ]
        
        return jsonify({
            "success": True,
            "data": result,
            "count": len(result)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@news_bp.route("/today/source", methods=["GET"])
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


@news_bp.route("/today/title", methods=["GET"])
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


@news_bp.route("/today/groups", methods=["GET"])
def get_title_groups():
    try:
        # Ambil semua title_index untuk hari ini
        today_titles = Title.query.with_entities(Title.title_index).filter(
            db.func.date(Title.date) == date.today()
        ).all()
        
        title_indices = [t.title_index for t in today_titles]
        
        if not title_indices:
            return jsonify({
                "success": True,
                "data": {},
                "count": 0
            }), 200
        
        # OPTIMASI: Batch query semua articles sekaligus (menghindari N+1 query)
        all_articles = (
            Article.query.with_entities(
                Article.id,
                Article.title,
                Article.source,
                Article.title_index
            )
            .filter(Article.title_index.in_(title_indices))
            .all()
        )
        
        # Grouping di Python (lebih cepat dari N queries)
        title_groups = {idx: [] for idx in title_indices}
        for a in all_articles:
            if a.title_index in title_groups:
                title_groups[a.title_index].append({
                    "id": a.id,
                    "title": a.title,
                    "source": a.source
                })
        
        return jsonify({
            "success": True,
            "data": title_groups,
            "count": len(title_groups)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@news_bp.route("/count-side", methods=["GET"])
def count_side():
    try:
        title_index = request.args.get('title_index', type=int)
        if not title_index:
            return jsonify({"success": False, "error": "No title_index provided"}), 400

        # OPTIMASI: Hitung langsung di database dengan SQL aggregate
        result = (
            db.session.query(
                func.count(Article.id).label("total"),
                func.sum(case((Article.ideology <= 0.25, 1), else_=0)).label("liberal"),
                func.sum(case((Article.ideology >= 0.75, 1), else_=0)).label("conservative"),
                func.sum(case(
                    ((Article.ideology > 0.25) & (Article.ideology < 0.75), 1), 
                    else_=0
                )).label("neutral")
            )
            .filter(Article.title_index == title_index)
            .first()
        )

        if not result or result.total == 0:
            return jsonify({
                "success": True, 
                "message": "No articles found for this title_index", 
                "count": 0
            }), 200

        return jsonify({
            "success": True,
            "counts": {
                "liberal": int(result.liberal or 0),
                "conservative": int(result.conservative or 0),
                "neutral": int(result.neutral or 0)
            },
            "total": int(result.total)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    

@news_bp.route("/top", methods=["GET"])
def top_news():
    try:
        limit = request.args.get('limit', default=5, type=int)

        # Ambil top title_index berdasarkan jumlah artikel (hanya untuk 1 hari terakhir)
        top_news_groups = (
            db.session.query(
                Article.title_index,
                func.count(Article.id).label("article_count")
            )
            .join(Title, Article.title_index == Title.title_index)
            .filter(Title.date >= func.curdate() - func.interval(1, 'DAY'))
            .group_by(Article.title_index)
            .order_by(desc("article_count"))
            .limit(limit)
            .all()
        )

        if not top_news_groups:
            return jsonify({
                "success": True,
                "message": "No news found for the specified date",
                "data": []
            }), 200

        # Ambil semua title_index
        title_indexes = [row.title_index for row in top_news_groups]

        # Ambil semua detail title sekaligus
        title_details_rows = Title.query.filter(Title.title_index.in_(title_indexes)).all()
        title_details_map = {t.title_index: t for t in title_details_rows}

        # OPTIMASI: Hitung ideology counts langsung di database dengan SQL aggregate
        ideology_counts = (
            db.session.query(
                Article.title_index,
                func.sum(case((Article.ideology <= 0.25, 1), else_=0)).label("liberal"),
                func.sum(case((Article.ideology >= 0.75, 1), else_=0)).label("conservative"),
                func.sum(case(
                    ((Article.ideology > 0.25) & (Article.ideology < 0.75), 1), 
                    else_=0
                )).label("neutral")
            )
            .filter(Article.title_index.in_(title_indexes))
            .group_by(Article.title_index)
            .all()
        )
        
        # Mapping counts
        counts_map = {
            row.title_index: {
                "liberal": int(row.liberal or 0),
                "conservative": int(row.conservative or 0),
                "neutral": int(row.neutral or 0)
            }
            for row in ideology_counts
        }

        # Susun hasil akhir
        result = []
        for group in top_news_groups:
            tidx = group.title_index
            title_detail = title_details_map.get(tidx)
            counts = counts_map.get(tidx, {"liberal": 0, "conservative": 0, "neutral": 0})

            if title_detail:
                result.append({
                    "title_index": tidx,
                    "title": title_detail.title,
                    "image": title_detail.image,
                    "all_summary": title_detail.all_summary,
                    "article_count": group.article_count,
                    "counts": counts
                })

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@news_bp.route("/cluster", methods=["GET"])
def get_cluster_news():
    try:
        cluster = request.args.get('cluster')
        if not cluster:
            return jsonify({"success": False, "error": "No cluster provided"}), 400

        news_items = (
            Title.query
            .filter(Title.cluster == cluster)
            .order_by(Title.date.desc())
            .all()
        )

        if not news_items:
            return jsonify({
                "success": True,
                "message": "No news found for this cluster",
                "count": 0
            }), 200

        result = [
            {
                'title_index': t.title_index,
                'title': t.title,
                'date': t.date,
                'all_summary': t.all_summary,
                'image': t.image
            }
            for t in news_items
        ]

        return jsonify({
            "success": True,
            "data": result,
            "total": len(result)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@news_bp.route("/search-title", methods=["GET"])
def search_title():
    try:
        search_query = request.args.get('query', '')
        if not search_query:
            return jsonify({"success": False, "error": "No search query provided"}), 400

        # Gunakan ilike (case-insensitive LIKE) untuk SQLAlchemy
        news_items = (
            Title.query
            .filter(Title.title.ilike(f"%{search_query}%"))
            .order_by(Title.date.asc())
            .all()
        )

        if not news_items:
            return jsonify({
                "success": True,
                "message": "No news found for this query",
                "count": 0
            }), 200

        result = [
            {
                'title_index': t.title_index,
                'title': t.title,
                'date': t.date,
                'all_summary': t.all_summary,
                'image': t.image
            }
            for t in news_items
        ]

        return jsonify({
            "success": True,
            "data": result,
            "total": len(result)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500