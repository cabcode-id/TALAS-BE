def test_get_today_source_counts(client, ):
    res = client.get("/news/today/source")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert any(d["source"] == "Kompas" for d in data["data"])

def test_get_today_titles(client,):
    res = client.get("/news/today/title")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["count"] >= 1
    assert "title" in data["data"][0]

def test_get_title_groups(client, ):
    res = client.get("/news/today/groups")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert isinstance(data["data"], dict)
    assert "1" in [str(k) for k in data["data"].keys()]
