#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import render_template, request, flash, redirect, url_for
import logging
from logging import Formatter, FileHandler
from forms import *
from datetime import datetime
from sys import exc_info


from models import *
from filters import format_datetime



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


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
    """
    Renders venues page with appropriate data and data structure. Venues are grouped
    by city.
    """
    data = []
    try:
        venues = db.session.query(Venue).order_by(Venue.city).all()
        locations = {(venue.city, venue.state) for venue in venues}
        data = [{
            'city': location[0],
            'state': location[1],
            'venues': [{
                'id': local_venue.id,
                'name': local_venue.name,
                'num_upcoming_shows': db.session.query(Show).join(Venue).filter(Show.start_time <= datetime.now(), Venue.id == local_venue.id).count()
            } for local_venue in Venue.query.filter_by(city=location[0]).all()]
        } for location in locations]
    except:
        print(exc_info())
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    """
    Implements search for venues, supporting partial, case-insensitive searches.
    """
    search_term = request.form.get('search_term', '')
    results = db.session.query(Venue).filter(
        Venue.name.ilike(f'%{search_term}%')).all()
    response = {
        "count": len(results),
        "data": [{
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": db.session.query(Show).filter(result.id == Show.venue_id and Show.start_time > datetime.now()).count(),
        }for result in results]
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """
    @param: venue_id
    Shows a specific venue by venue_id. The data structure given was considered in implementation.
    """
    venues = Venue.query.all()
    past_shows = db.session.query(Show).join(Venue).filter(Show.start_time <= datetime.now(), Venue.id == venue_id).all()
    upcoming_shows = db.session.query(Show).join(Venue).filter(Show.start_time > datetime.now(), Venue.id == venue_id).all()
    unfiltered_data = [{
        'id': venue.id,
        'name': venue.name,
        'genres': venue.genres[1:-1].split(','),
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': [{
            'artist_id': show.artist_id,
            'artist_name': Artist.query.get(show.artist_id).name,
            'artist_image_link': Artist.query.get(show.artist_id).image_link,
            'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
        } for show in past_shows],
        'upcoming_shows': [{
            'artist_id': show.artist_id,
            'artist_name': Artist.query.get(show.artist_id).name,
            'artist_image_link': Artist.query.get(show.artist_id).image_link,
            'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
        } for show in upcoming_shows],
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    } for venue in venues]
    # debug from starter code if there's a bug.
    data = list(filter(lambda d: d['id'] ==
                       venue_id, unfiltered_data))[0]
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    """
    Handles the creation of a new venue.
    """
    form = VenueForm(request.form)
    # A dict that holds form data
    data = {
        'name': form.name.data,
        'genres': form.genres.data,
        'address': form.address.data,
        'city': form.city.data,
        'state': form.state.data,
        'phone': form.phone.data,
        'image_link': form.image_link.data,
        'facebook_link': form.facebook_link.data,
        'seeking_talent': form.seeking_talent.data,
        'seeking_description': form.seeking_description.data,
        'website': form.website.data
    }
    # Venue creation and addition to the db, with any exceptions handled.
    try:
        venue = Venue(
            name=data['name'],
            genres=data['genres'],
            address=data['address'],
            city=data['city'],
            state=data['state'],
            phone=data['phone'],
            image_link=data['image_link'],
            facebook_link=data['facebook_link'],
            seeking_talent=data['seeking_talent'],
            seeking_description=data['seeking_description'],
            website=data['website']
        )
        venues = [ven[0] for ven in db.session.query(
            Venue.name).filter_by(city=venue.city).all()]
        if venue.name not in venues:
            db.session.add(venue)
            db.session.commit()
            # on successful db insert, flash success
            flash('Venue ' + data['name'] + ' was successfully listed!')
        else:
            flash('Venue ' + data['name'] + ' already exists')
    except:
        flash('An error occurred. Venue ' +
              data['name'] + ' could not be listed.')
        db.session.rollback()
        print(exc_info())
    finally:
        db.session.close()
    return redirect(url_for('index'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """
    @param: venue_id
    Handles the deletion of any venue. AJAX UI support was implemented in the appropriate 
    show_venue template
    """
    try: 
        Show.query.filter_by(venue_id=venue_id).delete()
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
        print(exc_info())
    finally: 
        db.session.close()
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    """
    Shows all artists.
    """
    artists = Artist.query.all()
    data = [{
        'id': artist.id,
        'name': artist.name
    } for artist in artists]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    """
    Implements search for artists, supporting partial, case-insensitive searches.
    """
    search_term = request.form.get('search_term', '')
    results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    response = {
        "count": len(results),
        "data": [{
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": Show.query.filter(Show.artist_id == result.id and Show.start_time > datetime.now()),
        } for result in results]
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """
    @param: artist_id
    Shows a specific artist by artist_id. The data structure given was considered in implementation.
    """
    artists = Artist.query.all()
    past_shows = db.session.query(Show).join(Artist).filter(Show.start_time <= datetime.now(), Artist.id == artist_id).all()
    upcoming_shows = db.session.query(Show).join(Artist).filter(Show.start_time > datetime.now(), Artist.id == artist_id).all()
    unfiltered_data = [{
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres[1:-1].split(','),
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': [{
            'venue_id': show.venue_id,
            'venue_name': Venue.query.get(show.venue_id).name,
            'venue_image_link': Venue.query.get(show.venue_id).image_link,
            'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
        } for show in past_shows],
        'upcoming_shows': [{
            'venue_id': show.venue_id,
            'venue_name': Venue.query.get(show.venue_id).name,
            'venue_image_link': Venue.query.get(show.venue_id).image_link,
            'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
        } for show in upcoming_shows],
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    } for artist in artists]
    
    data = list(filter(lambda d: d['id'] ==
                       artist_id, unfiltered_data))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    # Creating a form instance pre-populated with the artist fields.
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    """
    Handles updates to an existing artist
    """
    try:
        form = ArtistForm(request.form)
        artist = Artist.query.get(artist_id)
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.website = form.website.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        db.session.rollback()
        print(exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try: 
        form = VenueForm(request.form)
        venue = Venue.query.get(venue_id)
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.genres = form.genres.data
        venue.phone = form.phone.data
        venue.image_link = form.image_link.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        db.session.rollback()
        print(exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    data = {
        'name': form.name.data,
        'genres': form.genres.data,
        'city': form.city.data,
        'state': form.state.data,
        'phone': form.phone.data,
        'image_link': form.image_link.data,
        'facebook_link': form.facebook_link.data,
        'seeking_talent': form.seeking_venue.data,
        'seeking_description': form.seeking_description.data,
        'website': form.website.data
    }
    try:
        artist = Artist(
            name=data['name'],
            genres=data['genres'],
            city=data['city'],
            state=data['state'],
            phone=data['phone'],
            image_link=data['image_link'],
            facebook_link=data['facebook_link'],
            seeking_venue=data['seeking_talent'],
            seeking_description=data['seeking_description'],
            website=data['website']
        )
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + data['name'] + ' was successfully listed!')
    except:
        flash('An error occurred. Artist ' +
              data['name'] + ' could not be listed.')
        db.session.rollback()
        print(exc_info())
    finally:
        db.session.close()
    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = [{
        'venue_id': show.venue_id,
        'venue_name': Venue.query.get(show.venue_id).name,
        'artist_id': show.artist_id,
        'artist_name': Artist.query.get(show.artist_id).name,
        'artist_image_link': Artist.query.get(show.artist_id).image_link,
        'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
    }for show in shows]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    data = {
        'artist_id': form.artist_id.data,
        'venue_id': form.venue_id.data,
        'start_time': form.start_time.data
    }
    try:
        show = Show(
            artist_id = data['artist_id'],
            venue_id = data['venue_id'],
            start_time = data['start_time']
        )
        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash(f'Show by {Artist.query.get(show.artist_id).name} on {show.start_time.strftime("%d/%m/%Y, %H:%M")} at {Venue.query.get(show.venue_id).name} has been listed successfully!')
    except:
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
        print(exc_info())
    finally:
        db.session.close()
    return redirect(url_for('index'))



@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
