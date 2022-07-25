# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
from logging import Formatter, FileHandler

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, abort
from flask_migrate import Migrate
from flask_moment import Moment

from forms import *
from models import *
from utils import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    # retrieve 5 most recent artists from database
    latest_artists = Artist.query.order_by(Artist.id.desc()).limit(5)

    # retrieve 5 most recent venues from database
    latest_venues = Venue.query.order_by(Venue.id.desc()).limit(5)
    return render_template('pages/home.html', latest_artists=latest_artists, latest_venues=latest_venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # fetch all venues from db
    db_venues = Venue.query.all()

    # group venues by city and state
    data = []

    # for each venue in venues
    for venue in db_venues:
        # extract city
        city = venue.city

        # extract state
        state = venue.state

        # count upcoming shows for each venue
        num_upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(
            Show.start_time > datetime.now()).count()

        # build venue venues data
        venue_data = {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': num_upcoming_shows
        }

        # check if city and state already in data, if not add it
        if not any(d['city'] == city and d['state'] == state for d in data):
            data.append({
                'city': city,
                'state': state,
                'venues': [venue_data]
            })
        # if city and state already in data, add venue data to existing city and state
        else:
            for d in data:
                if d['city'] == city and d['state'] == state:
                    d['venues'].append(venue_data)
                    break

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # get search term from form data
    search_term = request.form.get('search_term', '')
    city, state = get_search_parts(request)
    if city and state:
        # get venues from db that match search term
        venues_results = Venue.query.filter(Venue.city.ilike(f'%{city}%')).filter(
            Venue.state.ilike(f'%{state}%')).all()
    else:
        # search for venues whose name contains search term
        venues_results = Venue.query.with_entities(Venue.id, Venue.name, Venue.shows).filter(
            Venue.name.ilike('%' + search_term + '%')).all()

    # build venues results mapped data
    data = []

    # for each venue in venues
    for venue in venues_results:
        # count number of upcoming shows for each venue
        num_upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now()).count()

        # build venue data
        data.append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': num_upcoming_shows
        })

    # build final response data
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_venues.html',
                           results=response,
                           search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id

    # retrieve venue that matches the venue_id
    venue = Venue.query.get_or_404(venue_id)

    # retrieve upcoming shows for venue
    upcoming_shows = Show.query.with_entities(
        Show.artist_id,
        Show.venue_id,
        Artist.name.label('artist_name'),
        Artist.image_link.label('artist_image_link'),
        Show.start_time
    ).join(Artist, Artist.id == Show.artist_id).filter(Show.venue_id == venue_id).filter(
        Show.start_time > datetime.now()).all()

    # retrieve past shows for venue
    past_shows = Show.query.with_entities(
        Show.artist_id,
        Show.venue_id,
        Artist.name.label('artist_name'),
        Artist.image_link.label('artist_image_link'),
        Show.start_time
    ).join(Artist, Artist.id == Show.artist_id).filter(Show.venue_id == venue.id).filter(
        Show.start_time < datetime.now()).all()

    # build venue data
    data = {
        **venue.__dict__,
        **{
            'upcoming_shows': upcoming_shows,
            'upcoming_shows_count': len(upcoming_shows),
            'past_shows': past_shows,
            'past_shows_count': len(past_shows)
        }}

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # retrieve venue form data
    form = VenueForm(request.form)

    # check if form is valid
    if form.validate():
        try:
            # create new venue with form data
            venue = Venue(**form.data)

            # add new venue to db
            db.session.add(venue)
            db.session.commit()

            # flash success message
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except Exception as e:
            db.session.rollback()
            print(e)
            # flash error message
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()

    else:
        return render_template('forms/new_venue.html', form=form)

    return redirect(url_for('index'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # retrieve venue that matches the venue_id
    venue = Venue.query.get_or_404(venue_id)
    error = False
    try:
        # delete venue from db
        db.session.delete(venue)
        db.session.commit()
        # flash success message
        flash('Venue ' + venue.name + ' was successfully deleted!')
    except Exception as e:
        db.session.rollback()
        error = True
        print(e)
        # flash error message
        flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')
    finally:
        db.session.close()
        if error:
            abort(500)

    return jsonify({'success': True})


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.with_entities(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # search term from form data
    search_term = request.form.get('search_term', '')
    city, state = get_search_parts(request)

    # if city and state are specified, search for artists in that city and state
    if city and state:
        # get artists from db that match search term
        artists_results = Artist.query.filter(Artist.city.ilike(f'%{city}%')).filter(
            Artist.state.ilike(f'%{state}%')).all()
    else:
        # search for artists whose name contains search term
        artists_results = Artist.query.with_entities(Artist.id, Artist.name, Artist.shows).filter(
            Artist.name.ilike('%' + search_term + '%')).all()

    # num of upcoming shows for each artist
    data = []
    for artist in artists_results:
        num_upcoming_shows = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time > datetime.now()).count()
        data.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': num_upcoming_shows
        })

    response = {
        "count": len(artists_results),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get_or_404(artist_id)

    # upcoming shows for artist
    upcoming_shows = Show.query.with_entities(
        Show.venue_id,
        Venue.name.label('venue_name'),
        Venue.image_link.label('venue_image_link'),
        Show.start_time
    ).join(Venue, Venue.id == Show.venue_id).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()
    ).all()

    # past shows for artist
    past_shows = Show.query.with_entities(
        Show.venue_id,
        Venue.name.label('venue_name'),
        Venue.image_link.label('venue_image_link'),
        Show.start_time
    ).join(Venue, Venue.id == Show.venue_id).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).all()

    data = {
        **artist.__dict__,
        **{
            'upcoming_shows': upcoming_shows,
            'upcoming_shows_count': len(upcoming_shows),
            'past_shows': past_shows,
            'past_shows_count': len(past_shows)
        }
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    # fill form with artist data
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # retrieve artist with artist_id
    artist = Artist.query.get_or_404(artist_id)
    # retrieve artist form data
    form = ArtistForm(request.form)

    try:
        # update artist with form data
        form.populate_obj(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # retrieve venue with venue_id or 404
    venue = Venue.query.get_or_404(venue_id)
    # retrieve venue form data
    form = VenueForm(request.form)
    # check if form is valid
    if form.validate():
        try:
            # update venue with form data
            form.populate_obj(venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully updated!')
        except Exception as e:
            db.session.rollback()
            print(e)
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
        finally:
            db.session.close()
    else:
        return render_template('forms/edit_venue.html', form=form, venue=venue)

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # retrieve artist form data
    form = ArtistForm(request.form)

    # check if form is valid
    if form.validate():
        try:
            artist = Artist(**form.data)
            db.session.add(artist)
            db.session.commit()
            # on successful db insert, flash success
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        except Exception as e:
            db.session.rollback()
            print(e)
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()

    else:
        return render_template('forms/new_artist.html', form=form)

    return redirect(url_for('index'))


@app.route('/artists/<int:artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    try:
        db.session.delete(artist)
        db.session.commit()
        flash('Artist ' + artist.name + ' was successfully deleted!')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash('An error occurred. Artist ' + artist.name + ' could not be deleted.')
    finally:
        db.session.close()

    return jsonify({'success': True})


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    data = Show.query.with_entities(
        Show.venue_id,
        Show.artist_id,
        Artist.name.label('artist_name'),
        Venue.name.label('venue_name'),
        Artist.image_link.label('artist_image_link'),
        Show.start_time
    ).join(
        Venue,
        Venue.id == Show.venue_id
    ).join(Artist, Artist.id == Show.artist_id).all()

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # retrieve show form data
    form = ShowForm(request.form)

    try:
        show = Show(**form.data)
        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


def get_search_parts(request):
    search_term = request.form.get('search_term', '')
    search_parts = search_term.strip().replace(', ', ',').split(',')
    if len(search_parts) == 2:
        # get city and state from search term
        city, state = search_parts
        return city, state
    return None, None


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
