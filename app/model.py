from app import db

class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(255))
    url = db.Column(db.String(500))
    image = db.Column(db.String(500))
    date = db.Column(db.String(100))
    content = db.Column(db.Text)
    embedding = db.Column(db.Text)  
    bias = db.Column(db.String(50))
    hoax = db.Column(db.String(50))
    ideology = db.Column(db.String(50))
    title_index = db.Column(db.Integer, db.ForeignKey('title.title_index'), index=True)

class Title(db.Model):
    __tablename__ = 'title'
    id = db.Column(db.Integer, primary_key=True)
    title_index = db.Column(db.Integer, unique=True)
    title = db.Column(db.String(255))
    cluster = db.Column(db.String(50))
    all_summary = db.Column(db.Text)
    analysis = db.Column(db.Text)
    keyword = db.Column(db.Text)
    date = db.Column(db.DateTime)
    image = db.Column(db.String(255))