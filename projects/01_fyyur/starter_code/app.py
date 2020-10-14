#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from datetime import datetime
from flask import (
  Flask, 
  render_template, 
  request, 
  Response, 
  flash, 
  redirect, 
  url_for, 
  jsonify, 
  abort,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import ShowForm, ArtistForm, VenueForm
from flask_migrate import Migrate
from models import Show, Venue, Artist
import sys
from models import db
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  venues = Venue.query.all()
  for venue in venues:
    inserted = False
    new_data = {
      'city' : venue.city,
      'state' : venue.state,
      'venues' : [{
        'id' : venue.id,
        'name' : venue.name,
      }]
    }
    for old_data in data:
      if(old_data['city'] == new_data['city'] and old_data['state'] == new_data['state']):
        old_data['venues'].append(new_data['venues'][0])
        inserted = True
        break
    if not inserted:
      data.append(new_data)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    'count' : 0,
    'data' : [],
  }
  search_name = "%{}%".format(request.form.get('search_term'))
  venues = Venue.query.filter(Venue.name.ilike(search_name)).all()
  for venue in venues:
    response['count'] += 1
    new_data = {
      'id' : venue.id,
      'name' : venue.name,
    }
    response['data'].append(new_data)
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)

  if venue is None:
    abort(404)

  past_shows = []
  upcoming_shows = []

  for show in venue.shows:
    artist_info = {
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    if show.start_time < datetime.now():
      past_shows.append(artist_info)
    else:
      upcoming_shows.append(artist_info)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  form = VenueForm()
  try:
    if form.validate_on_submit():
      new_venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        genres = ','.join(form.genres.data),
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website = form.website.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )
      db.session.add(new_venue)
      db.session.commit()
    else:
      error = True
      for fieldName, errorMessages in form.errors.items():
        for err in errorMessages:
          print(err, file=sys.stdout)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  # on successful db insert, flash success
  if(error):
    flash('Error!')
    return render_template('forms/new_venue.html', form=form)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('index'))
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  result = { 'success' : True }
  try:
    venue = Venue.query.get(venue_id)
    if venue is None:
      abort(404)
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Delete!')
  except:
    db.session.rollback()
    flash('Error!')
    result['sucess'] = False
    print(sys.exc_info())
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return jsonify(result)

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=[]
  artists = Artist.query.all()
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    'count' : 0,
    'data' : [],
  }
  search_name = "%{}%".format(request.form.get('search_term'))
  artists = Artist.query.filter(Venue.name.ilike(search_name)).all()
  for artist in artists:
    response['count'] += 1
    new_data = {
      'id' : artist.id,
      'name' : artist.name,
    }
    response['data'].append(new_data)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)

  if artist is None:
    abort(404)

  past_shows = []
  upcoming_shows = []

  for show in artist.shows:
    venue_info = {
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    if show.start_time < datetime.now():
      past_shows.append(venue_info)
    else:
      upcoming_shows.append(venue_info)

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)

  if artist is None:
    abort(404)

  form = ArtistForm(obj=artist)
  form.genres.data = artist.genres.split(',')
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  if artist is None:
    abort(404)

  try:
    if form.validate_on_submit():
      form.populate_obj(artist)
      artist.genres = ','.join(form.genres.data)
      db.session.commit()
    else:
      error = True
      for fieldName, errorMessages in form.errors.items():
        for err in errorMessages:
          print(err, file=sys.stdout)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('Error!')
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  else:
    flash('Success!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)

  if venue is None:
    abort(404)

  form = VenueForm(obj=venue)
  form.genres.data = venue.genres.split(',')
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue is None:
    abort(404)

  try:
    if form.validate_on_submit():
      form.populate_obj(venue)
      venue.genres = ','.join(form.genres.data)
      db.session.commit()
    else:
      error = True
      for fieldName, errorMessages in form.errors.items():
        for err in errorMessages:
          print(err, file=sys.stdout)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('Error!')
    return render_template('forms/edit_venue.html', form=form, venue=venue)
  else:
    flash('Venue Id : ' + str(venue_id) + ' edited!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  error = False
  try:
    form = ArtistForm()
    if form.validate_on_submit():
      new_artist = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = ','.join(form.genres.data),
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website = form.website.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data,
      )
      db.session.add(new_artist)
      db.session.commit()
    else:
      error = True
      for fieldName, errorMessages in form.errors.items():
        for err in errorMessages:
          print(err, file=sys.stdout)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if(error):
    flash('Error!')
    return render_template('forms/new_artist.html', form=form)
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return redirect(url_for('index'))
  return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]
  shows = Show.query.all()
  for show in shows:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  error = False
  form = ShowForm()
  try:
    if form.validate_on_submit():
      new_show = Show(
        start_time = form.start_time.data
      )
      venue = Venue.query.get(form.venue_id.data)
      artist = Artist.query.get(form.artist_id.data)
      if venue is None or artist is None:
        flash('Check Id')
        return render_template('forms/new_show.html', form=form)
      new_show.venue = venue
      new_show.artist = artist
      venue.shows.append(new_show)
      artist.shows.append(new_show)
      db.session.add(new_show)
      db.session.commit()
    else:
      error = True
      for fieldName, errorMessages in form.errors.items():
        for err in errorMessages:
          print(err, file=sys.stdout)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  # on successful db insert, flash success
  if(error):
    flash('Error!')
    return render_template('forms/new_show.html', form=form)
  else:
    flash('Show was successfully listed!')
    return redirect(url_for('index'))
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('forms/new_show.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
