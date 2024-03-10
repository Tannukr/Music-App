from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

album_association = db.Table(
    'album_association',
    db.Column('album_id', db.Integer, db.ForeignKey('album_creator.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('upload_song_creator.id'), primary_key=True),
)

class PlaylistSong(db.Model):
    __tablename__ = 'playlist_song_association'
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True)
    #song_id = db.Column(db.Integer, db.ForeignKey('upload_song_creator.id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('upload_song_creator.id', ondelete='CASCADE'), nullable=False)

class album_creator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='albums')
    songs = db.relationship('upload_song_creator', secondary='album_association', back_populates='albums')
    image_url = db.Column(db.String(255))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    playlists = db.relationship('Playlist', back_populates='user')
    albums = db.relationship('album_creator', back_populates='user')
    is_creator = db.Column(db.Boolean, default=False)
    uploads = db.relationship('upload_song_creator', back_populates='user')
    is_blacklisted = db.Column(db.Boolean, default=False)

class upload_song_creator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    singer = db.Column(db.String(80), nullable=False)
    release_date = db.Column(db.String(80), nullable=False)
    lyrics = db.Column(db.String(350), nullable=False)
    genre = db.Column(db.String(80), nullable=False)
    image_url = db.Column(db.String(255))
  
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='uploads')
    playlists = db.relationship('Playlist', secondary='playlist_song_association', back_populates='songs')
    albums = db.relationship('album_creator', secondary='album_association', back_populates='songs')
    ratings = db.relationship('Rating', back_populates='song')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #song_id = db.Column(db.Integer, db.ForeignKey('upload_song_creator.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('upload_song_creator.id', ondelete='CASCADE'), nullable=False)
    
    
    song = db.relationship('upload_song_creator', back_populates='ratings')  

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='playlists')
    songs = db.relationship('upload_song_creator', secondary='playlist_song_association', back_populates='playlists')
    image_url = db.Column(db.String(255))
