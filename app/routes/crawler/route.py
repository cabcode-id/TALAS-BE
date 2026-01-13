from flask import Blueprint, request, jsonify
from app import db
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from app.services.crawlers import main as run_crawlers  
from app.model  import Article , Title
from app.services.analysis import (
    predict_cluster , cleaned_service , embedding_service, separate_service,
    mode_cluster as get_mode_cluster, generate_title_service, 
    summarize_service, analyze_service,
)       
from app.utils.mainfunctions import (
    predictBias, predictHoax, predictIdeology
)

crawler_bp = Blueprint('crawler', __name__)

@crawler_bp.route("/run", methods=["POST"])
def run_crawlers_endpoint():
    try:
        params = request.json or {}
        
        # Extract ?pantai, default False
        pantai = params.pop('pantai', False)
        parallel = params.pop('parallel', True)
        
        # Jalankan crawler
        results = run_crawlers(pantai=pantai, parallel=parallel, **params)
        
        if not results:
            return jsonify({
                "success": True, 
                "message": "Crawlers executed but no results were returned", 
                "count": 0
            }), 200
        
        # Masukkan hasil ke database menggunakan ORM
        inserted_count = 0
        for article in results:
            try:
                # Ambil data dengan fallback kosong
                title = article.get('title', '')
                source = article.get('source', '')
                url = article.get('url', '')
                image = article.get('image', '')
                date = article.get('date', '')
                content = article.get('content', '')
                
                # Lewati artikel tanpa title atau content
                if not title or not content:
                    continue
                
                # Buat objek Article baru
                new_article = Article(
                    title=title,
                    source=source,
                    url=url,
                    image=image,
                    date=date,
                    content=content
                )
                
                # Tambahkan ke session
                db.session.add(new_article)
                inserted_count += 1
                
            except Exception as article_error:
                print(f"Error inserting article: {str(article_error)}")
                continue
        
        # Commit semua sekaligus
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Crawlers executed and data inserted successfully",
            "total_results": len(results),
            "inserted_count": inserted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@crawler_bp.route("/update", methods=["GET"])
def update_articles():
    try:
        articles = Article.query.filter(Article.embedding.is_(None)).all()
        
        if not articles:
            return jsonify({
                "success": True, 
                "message": "No articles found with null embeddings", 
                "count": 0
            }), 200
        
        processed_count = 0
        updated_clusters = 0
        update_data = []

        def _run_parallel_services(article):
            results = {
                "cluster": None,
                "bias": None,
                "hoax": None,
                "cleaned": None,
                "embedding": None,
            }

            def _embedding_task():
                data_for_embedding = [{
                    "id": article.id,
                    "title": article.title,
                    "content": article.content
                }]
                embeddings = embedding_service(data_for_embedding)
                if embeddings and len(embeddings) > 0:
                    return json.dumps(embeddings[0])
                return None

            tasks = {
                "cluster": lambda: predict_cluster(article.content),
                "bias": lambda: predictBias(article.content),
                "hoax": lambda: predictHoax(article.content),
                "cleaned": lambda: cleaned_service(article.content),
                "embedding": _embedding_task,
            }

            max_workers = min(5, len(tasks))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(func): name for name, func in tasks.items()}
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        results[name] = future.result()
                    except Exception:
                        results[name] = None

            ideology_result = None
            if results["cleaned"]:
                ideology_result = predictIdeology(results["cleaned"])

            return {
                "cluster": results["cluster"],
                "bias": results["bias"],
                "hoax": results["hoax"],
                "cleaned": results["cleaned"],
                "ideology": ideology_result,
                "embedding": results["embedding"],
            }
        
        for article in articles:
            try:
                results = _run_parallel_services(article)
                
                # Kumpulkan hasil
                update_data.append({
                    'article': article,
                    'cluster': results['cluster'],
                    'bias': results['bias'],
                    'hoax': results['hoax'],
                    'cleaned': results['cleaned'],
                    'ideology': results['ideology'],
                    'embedding': results['embedding']
                })
                
                processed_count += 1
                
            except Exception as article_error:
                continue
        
        # Update database
        for item in update_data:
            article = item['article']
            if item['bias'] is not None:
                article.bias = item['bias']
            if item['hoax'] is not None:
                article.hoax = item['hoax']
            if item['cleaned'] is not None:
                article.cleaned = item['cleaned']
            if item['ideology'] is not None:
                article.ideology = item['ideology']
            if item['embedding'] is not None:
                article.embedding = item['embedding']

            # ⬇️ Update cluster langsung ke Title (jika article punya title_index)
            if item['cluster'] is not None and article.title_index:
                title_record = Title.query.filter_by(title_index=article.title_index).first()
                if title_record:
                    title_record.cluster = str(item['cluster'])  # simpan sebagai string
                    updated_clusters += 1


        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Processed {processed_count} articles. "
                       f"Updated cluster for {updated_clusters} Title records.",
            "total_articles": len(articles),
            "updated_clusters": updated_clusters
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@crawler_bp.route("/group", methods=["GET", "POST"])
def group_articles():
    try:
        articles = Article.query.filter(Article.title_index.is_(None)).all()
        if not articles:
            return jsonify({
                "success": True,
                "message": "No articles found with NULL title_index",
                "count": 0
            }), 200

        # Ambil data artikel
        articles_data = []
        for article in articles:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'embedding': json.loads(article.embedding) if article.embedding else None
            })
        # Dapatkan cluster index baru
        clusters = separate_service(articles_data)
        max_index = db.session.query(db.func.max(Title.title_index)).scalar() or 0
        offset = max_index + 1
        new_title_indices = [cluster + offset for cluster in clusters]
        unique_title_indices = set(new_title_indices)

        # STEP 1: Insert title indices dulu
        for idx in unique_title_indices:
            new_title = Title(title_index=idx)
            db.session.add(new_title)
        db.session.flush()

        # STEP 2: Update articles setelah title ada
        for article, new_idx in zip(articles, new_title_indices):
            article.title_index = new_idx

        # STEP 3: Commit sekali
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Successfully grouped {len(articles)} articles into {len(unique_title_indices)} clusters",
            "articles_count": len(articles),
            "clusters_count": len(unique_title_indices)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500



@crawler_bp.route("/process", methods=["GET", "POST"])
def process_articles():
    try:
        # Ambil title_index yang belum punya title
        title_records = Title.query.filter(
            (Title.title == None) | (Title.title == '')
        ).all()

        if not title_records:
            return jsonify({
                "success": True,
                "message": "No articles found with empty title",
                "count": 0
            }), 200

        processed_count = 0

        for record in title_records:
            title_index = record.title_index

            # Ambil semua artikel di grup ini
            group_articles = Article.query.filter_by(title_index=title_index).all()
            if not group_articles:
                continue

            # Format untuk API lain dan hitung cluster untuk setiap artikel
            formatted_articles = []
            cluster_results = []
            
            for article in group_articles:
                # Prediksi cluster untuk setiap artikel
                cluster_result = predict_cluster(article.content)
                cluster_results.append(cluster_result)

                formatted_articles.append({
                    'title': article.title,
                    'content': article.content,
                    'embedding': json.loads(article.embedding) if article.embedding else None,
                    'bias': article.bias,
                    'hoax': article.hoax,
                    'ideology': article.ideology,
                    'cluster': cluster_result  # Gunakan hasil prediksi langsung
                })

            # Hitung mode cluster dari hasil prediksi
            from collections import Counter
            if cluster_results:
                mode_cluster = Counter(cluster_results).most_common(1)[0][0]
            else:
                mode_cluster = None

            # title
            new_title = generate_title_service(formatted_articles)

            # summary
            all_summary = summarize_service(formatted_articles)

            # analyze
            analysis = analyze_service(formatted_articles)

            # Ambil image pertama yang ada
            image_link = next((a.image.strip() for a in group_articles if a.image and a.image.strip()), None)

            # Update tabel Title
            record.title = new_title
            record.cluster = mode_cluster
            record.all_summary = all_summary
            record.analysis = analysis
            record.date = datetime.now(timezone.utc)
            record.image = image_link

            processed_count += 1

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Successfully processed {processed_count} article groups",
            "total_groups": len(title_records),
            "processed_groups": processed_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
