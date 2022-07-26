from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venues', lazy='joined', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Artist id : {self.id} {self.name} >'

    @property
    def past_shows(self):
        return [show for show in self.shows if show.start_time < datetime.now()]

    @property
    def upcoming_shows(self):
        return [show for show in self.shows if show.start_time > datetime.now()]

    @property
    def num_past_shows(self):
        return len(self.past_shows)

    @property
    def num_upcoming_shows(self):
        return len(self.upcoming_shows)


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artists', lazy=True, cascade='all, delete-orphan')
    albums = db.relationship('Album', backref='artists', lazy='joined', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Artist id : {self.id} {self.name} >'

    @property
    def total_albums(self):
        return len(self.albums)

    @property
    def latest_released_album(self):
        return self.albums[-1]


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show id : {self.id} artist_id : {self.artist_id} venue_id : {self.venue_id} start_time : {self.start_time}>'


class Album(db.Model):
    __tablename__ = 'albums'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    name = db.Column(db.String)
    release_date = db.Column(db.DateTime, nullable=False)
    image_link = db.Column(db.String(500))
    songs = db.relationship('Song', backref='albums', lazy='joined', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Album id : {self.id} artist_id : {self.artist_id} name : {self.name}>'

    @property
    def total_tracks(self):
        return len(self.songs)


class Song(db.Model):
    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), nullable=False)
    name = db.Column(db.String)
    duration = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Song id : {self.id} album_id : {self.album_id} title : {self.title}>'

    @property
    def track_number(self):
        return self.album.songs.index(self) + 1

