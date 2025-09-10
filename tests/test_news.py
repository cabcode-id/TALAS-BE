def test_get_news(client):
    res = client.get("/news/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "data" in data

def test_get_news_detail(client):
    res = client.get("/news/detail?title_index=1")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["title"] == "Sample News"

def test_get_today_articles(client):
    res = client.get("/news/today")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["count"] >= 1

def test_get_today_source_counts(client):
    res = client.get("/news/today/source")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert any(item["source"] == "ExampleSource" for item in data["data"])

def test_count_side(client):
    res = client.get("/news/count-side?title_index=1")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "counts" in data


def test_get_cluster_news(client):
    res = client.get("/news/cluster?cluster=cluster-a")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True

def test_search_title(client):
    res = client.get("/news/search-title?query=Sample")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
