from flask import Flask,render_template,request,redirect,url_for,session,flash
from flask_bcrypt import Bcrypt
from flask_bcrypt import check_password_hash
from models import *
from sqlalchemy import or_ ,func,and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
import os 
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mymusic.sqlite3'  
app.secret_key = 'your_secret_key'

bcrypt = Bcrypt(app)
db.init_app(app)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        name = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        print(name, email, password)
        existing_user = User.query.filter_by(email=email).first()

        print(existing_user)
        if existing_user:
            print("User already Exists")
            flash("Email already registered")
            return redirect("/register")
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=name, email=email, password=hashed_password)
            print(new_user)
            db.session.add(new_user)
            db.session.commit()
            flash("You are now registered. Please login.")
            return redirect("/login")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        #is_creator = 'is_creator' in request.form
       
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                 
                
            }
            return redirect(url_for('user_dashboard'))
            

    return render_template('login.html')

@app.route('/creator_login', methods=['GET', 'POST'])
def creator_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        is_creator = 'is_creator' in request.form

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if user.is_blacklisted:
                flash("You are blacklisted and cannot log in.")
                return redirect(url_for('index'))

            session['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_creator': is_creator
            }

            
            user.is_creator = is_creator
            db.session.commit()

            if is_creator:
                return redirect(url_for('creator_dashboard'))

    return render_template('creator_login.html')

@app.route('/songs/<int:id>')
def songs(id):
    
    songs = upload_song_creator.query.filter_by(id=id).first()
    
    return render_template('songs.html', songs=songs)


@app.route('/lyrics/<int:id>')
def lyrics(id):
    songs = upload_song_creator.query.filter_by(id=id).first()
    return render_template('lyrics.html', songs=songs)

@app.route('/show_more')
def show_more():
    user = session.get('user')  
    if user is None:
        return redirect(url_for('login'))
    songs = upload_song_creator.query.all()
    print(songs)  # Check if data is printed in the console
    return render_template('show_more.html', songs=songs ,user=user)

@app.route('/logout' )
def logout():
    session.clear()
    return render_template("index.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "GET":
        return render_template("admin.html")
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "Tannu@gmail.com" and password == "1234":
            session['username'] = username
            return redirect('/admin_dashboard')
        else:
            flash("Invalid username or password.")
            return redirect('/admin')

    return redirect('/admin')


@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    
    total_users = User.query.count()
    total_all_creators = User.query.filter_by(is_creator=True).count()
    total_uploaded_songs = upload_song_creator.query.count()
    total_genres = db.session.query(func.count(upload_song_creator.genre.distinct())).scalar()
    total_albums = album_creator.query.count()
    all_songs = upload_song_creator.query.all()
    all_genres = db.session.query(upload_song_creator.genre.distinct()).all()
    all_albums = album_creator.query.all()
    all_users = User.query.all()
    all_creators = User.query.filter_by(is_creator=True).all()
   

    return render_template("admin_dashboard.html", 
                           total_users=total_users, 
                           total_uploaded_songs=total_uploaded_songs, 
                           total_genres=total_genres, 
                           total_albums=total_albums,
                           all_songs=all_songs,
                           all_genres=all_genres,
                           all_albums=all_albums,
                           all_users=all_users,
                           all_creators=all_creators,
                           total_all_creators=total_all_creators)


@app.route('/delete_song_admin/<int:song_id>', methods=['POST'])
def delete_song_admin(song_id):
    if 'username' in session and session['username'] == 'Tannu@gmail.com':
        song_to_delete = upload_song_creator.query.get(song_id)

        if song_to_delete:
            # Delete the song
            Rating.query.filter_by(song_id=song_id).delete()

            db.session.delete(song_to_delete)
            db.session.commit()

        #     flash('Song deleted successfully!')
        # else:
        #     flash('Failed to delete the song.')

        return redirect(url_for('tracks'))



@app.route('/tracks', methods=["GET"])
def tracks():
    all_songs = upload_song_creator.query.all()

    return render_template('tracks.html', all_songs=all_songs)
    
@app.route("/upload_song", methods=["GET", "POST"])
def upload_song():
    user = session.get('user')

    if not user or not user['is_creator']:
        flash("User not found or not authorized. Please log in as a creator.")
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        singer = request.form["singer"]
        release_date = request.form["releasedate"]
        lyrics = request.form["lyrics"]
        genre = request.form["genre"]

        # Get the uploaded image file
        file = request.files['file']

        # Use secure_filename to ensure a safe filename
        filename = secure_filename(file.filename)

        # Save the image file to the configured UPLOAD_FOLDER
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Now you can use the filename in the rest of your code

        new_song = upload_song_creator(
            title=title, singer=singer, release_date=release_date,
            lyrics=lyrics, genre=genre, user_id=user['id'],
            image_url=url_for('static', filename='images/' + filename)
        )

        db.session.add(new_song)
        db.session.commit()

        flash("Song uploaded successfully!")
        return redirect("/creator_dashboard")

    return render_template("upload_song.html")

@app.route('/delete_song/<int:song_id>', methods=['POST'])
def delete_song(song_id):
    user = session.get('user')  
    if user['is_creator']:
        song_to_delete = upload_song_creator.query.get(song_id)

        if song_to_delete and  Rating.query.filter_by(song_id=song_id).delete():
        
            db.session.delete(song_to_delete)
            db.session.commit()

            flash('Song deleted successfully!')
        else:
            flash('Failed to delete the song.')

    return redirect(url_for('creator_dashboard'))

@app.route("/edit_song/<int:song_id>", methods=["GET", "POST"])
def edit_song(song_id):
    user = session.get('user')
    if user['is_creator']:
        song_to_edit = upload_song_creator.query.get(song_id)
        if request.method == "POST":
            song_to_edit.title = request.form["title"]
            song_to_edit.singer = request.form["singer"]
            song_to_edit.release_date = request.form["releasedate"]
            song_to_edit.lyrics = request.form["lyrics"]
            song_to_edit.genre = request.form["genre"]

            db.session.commit()

            flash("Song updated successfully!")
            return redirect("/creator_dashboard")

    return render_template("edit_song.html", song=song_to_edit)


@app.route('/user_dashboard')
def user_dashboard():
    user = session.get('user')
    if not user or 'id' not in user:
        flash("You must be logged in to access the user dashboard.")
        return redirect(url_for('login'))
    user_playlists = Playlist.query.filter_by(user_id=user['id']).all()
    print("User Playlists:", user_playlists)

    songs = upload_song_creator.query.all()
    print("All Songs:", songs)

    avg_ratings = {}
    for song in songs:
        ratings = [rating.value for rating in song.ratings]
        avg_rating = round(sum(ratings) / len(ratings)) if len(ratings) > 0 else 0
        avg_ratings[song.id] = avg_rating

    sorted_songs = sorted(songs, key=lambda song: avg_ratings[song.id], reverse=True)

    return render_template("user_dashboard.html", user=user, songs=sorted_songs, playlists=user_playlists, avg_ratings=avg_ratings)

@app.route('/creator_dashboard', methods=["GET", "POST"])
def creator_dashboard():
    user = session.get('user')
    if user is None:
        return redirect(url_for('login'))

    if user and user['is_creator']:
        creator_name = user['username']
        
        num_uploaded_songs = upload_song_creator.query.filter_by(user_id=user['id']).count()
        num_uploaded_albums = album_creator.query.filter_by(user_id=user['id']).count()
        avg_rating = db.session.query(func.avg(Rating.value)).join(upload_song_creator).filter(upload_song_creator.user_id == user['id']).scalar()
        avg_rating = round(avg_rating, 2) if avg_rating else 0.0

        user_albums = album_creator.query.filter_by(user_id=user['id']).all()
        songs = upload_song_creator.query.filter_by(user_id=user['id']).all()

        return render_template('creator_dashboard.html', user=user, creator_name=creator_name, albums=user_albums, songs=songs, num_uploaded_songs=num_uploaded_songs, num_uploaded_albums=num_uploaded_albums, avg_rating=avg_rating)

    else:
        return redirect(url_for('user_homepage'))

@app.route('/search_results', methods=['GET'])
def search():
    user = session.get('user')
    if user is None:
        return redirect(url_for('login'))

    query = request.args.get('query', default='', type=str)

    songs_results = upload_song_creator.query.filter(
        or_(
            upload_song_creator.title.ilike(f"%{query}%"),
            upload_song_creator.singer.ilike(f"%{query}%"),
            upload_song_creator.genre.ilike(f"%{query}%"),
        )
    ).all()

   
    playlists_results = Playlist.query.filter(
        (Playlist.name.ilike(f"%{query}%")) &
        (Playlist.user_id == user['id'])
    ).all()

    albums_results = album_creator.query.filter(album_creator.name.ilike(f"%{query}%")).all()

    return render_template('search_results.html', songs_results=songs_results, playlists_results=playlists_results,
                           albums_results=albums_results, query=query, user=user)


    
@app.route('/user_homepage', methods=["GET", "POST"])
def user_homepage():
    user = session.get('user')
    
        # Render the user homepage
    return render_template('user_homepage.html', user=user)

   
@app.route("/album", methods=["GET", "POST"])
def album():
    user = session.get('user')
    new_album = None

    # Check if the user is a creator
    if user['is_creator']:
        
        if request.method == "POST":
            album_name = request.form.get('albumName')  
            new_album = album_creator(name=album_name, user_id=user['id'])
            file = request.files['file']

        
            filename = secure_filename(file.filename)

        
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url=url_for('static', filename='images/' + filename)

            db.session.add(new_album)
            db.session.commit()
            selected_song_ids = request.form.getlist('selected_songs[]')

            for song_id in selected_song_ids:
                song = upload_song_creator.query.get(song_id)
                if song:
                    new_album.songs.append(song)

            db.session.commit()

            flash("Album created successfully!")
            return redirect(url_for('creator_dashboard'))

       
        all_songs = upload_song_creator.query.filter_by(user_id=user['id']).all()


        return render_template('album.html', user=user, creator_name=user['username'], songs=all_songs)


    
    flash("You do not have permission to create albums.")
    return redirect(url_for('user_homepage'))

@app.route('/albumpage/<int:album_id>')
def albumpage(album_id):
    user = session.get('user')
    album = album_creator.query.filter_by(id=album_id, user_id=user['id']).first()

    if album:
        creator_name = user['username']
        creator_songs = upload_song_creator.query.filter_by(user_id=user['id']).all()
        available_songs = [song for song in creator_songs if song not in album.songs]

        return render_template("albumpage.html", creator_name=creator_name, album=album, available_songs=available_songs)
    else:
        flash("Error: Album not found.")
        return redirect(url_for('user_dashboard'))


@app.route('/remove_song_from_album/<int:album_id>/<int:song_id>', methods=['GET', 'POST'])
def remove_song_from_album(album_id, song_id):
    album = album_creator.query.get(album_id)
    song = upload_song_creator.query.get(song_id)

    if album and song:
        album.songs.remove(song)
        db.session.commit()
        flash("Song removed from the album.")
    else:
        flash("Error: Album or song not found.")

    return redirect(url_for('albumpage', album_id=album_id))

@app.route('/add_songs_to_album/<int:album_id>', methods=['POST'])
def add_songs_to_album(album_id):
    album = album_creator.query.get(album_id)

    if album:
        selected_song_ids = request.form.getlist('selected_songs[]')

        for song_id in selected_song_ids:
            song = upload_song_creator.query.get(song_id)
            if song:
                album.songs.append(song)

        db.session.commit()
        flash("Songs added to the album.")
    else:
        flash("Error: Album not found.")

    return redirect(url_for('albumpage', album_id=album_id)) 

@app.route('/delete_album/<int:album_id>', methods=['POST'])
def delete_album(album_id):
    user = session.get('user')
    album = album_creator.query.filter_by(id=album_id, user_id=user['id']).first()

    if album:
        db.session.delete(album)
        db.session.commit()

    return redirect(url_for('album'))



@app.route("/create_playlist_user", methods=["GET", "POST"])
def create_playlist_user():
    user = session.get('user')
    user_id = user.get('id')  
    if user is None:
        return redirect(url_for('login'))

    new_playlist = None
    if request.method == "POST":
        playlist_name = request.form.get('playlist_name')
        file = request.files['file']

        
        filename = secure_filename(file.filename)

        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_url=url_for('static', filename='images/' + filename)


        if not playlist_name:
            flash("Playlist name cannot be empty.")
            return redirect(url_for('create_playlist_user'))

        new_playlist = Playlist(name=playlist_name, user_id=user_id)
        db.session.add(new_playlist)
        db.session.commit()
        
        selected_song_ids = request.form.getlist('selected_songs[]')

        # for song_id in selected_song_ids:
        #     song = upload_song_creator.query.get(song_id)
        #     if song:
        #         playlist_song = PlaylistSong(playlist_id=new_playlist.id, song_id=song.id)
        #         db.session.add(playlist_song,image_url=url_for('static', filename='images/' + filename))

        # db.session.commit()

        return redirect(url_for('user_dashboard', playlist_id=new_playlist.id))

    all_songs = upload_song_creator.query.all()

    return render_template('create_playlist_user.html', user=user, songs=all_songs)

@app.route('/playlist_details/<int:playlist_id>')
def playlist_details(playlist_id):
    user = session.get('user')
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=user['id']).first()

    if playlist:
        playlist_songs = playlist.songs
        all_songs = upload_song_creator.query.all()
        available_songs = [song for song in all_songs if song not in playlist_songs]

        return render_template("playlist_details.html", playlist=playlist, playlist_songs=playlist_songs, available_songs=available_songs)
    else:
        flash("Playlist not found.")
        return redirect(url_for('playlist_details'))
        
@app.route('/remove_song_from_playlist/<int:playlist_id>/<int:song_id>', methods=['GET', 'POST'])
def remove_song_from_playlist(playlist_id, song_id):
    playlist = Playlist.query.get(playlist_id)
    song = upload_song_creator.query.get(song_id)

    if playlist and song:
        playlist_song = db.session.query(PlaylistSong).filter_by(playlist_id=playlist.id, song_id=song.id).first()
        if playlist_song:
            db.session.delete(playlist_song)
            db.session.commit()
        else:
            flash("Song not found in the playlist.")
    else:
        flash("Error: Playlist or song not found.")

    return redirect(url_for('playlist_details', playlist_id=playlist_id))


@app.route('/delete_playlist/<int:playlist_id>', methods=['POST'])
def delete_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)

    if playlist:
        db.session.delete(playlist)
        db.session.commit()

    return redirect(url_for('user_dashboard'))


@app.route('/admin_album')
def admin_album():
    
    if 'username' not in session or session['username'] != 'Tannu@gmail.com':
        flash("You do not have permission to access this page.")
        return redirect(url_for('admin_dashboard'))

    all_creators = User.query.filter_by(is_creator=True).all()

    all_albums = []
    for creator in all_creators:
        creator_albums = album_creator.query.filter_by(user_id=creator.id).all()
        for album in creator_albums:
            album_info = {
                'creator': creator,
                'album': album,
                'songs': album.songs
            }
            all_albums.append(album_info)

    return render_template('admin_album.html', all_albums=all_albums)

@app.route('/admin_delete_album/<int:album_id>', methods=['POST'])
def admin_delete_album(album_id):
    if 'username' in session and session['username'] == 'Tannu@gmail.com':
        album = album_creator.query.get(album_id)

        if album:
            
            db.session.delete(album)
            db.session.commit()
            flash('Album deleted successfully!')
        else:
            flash('Album not found.')

        return redirect(url_for('admin_album'))
    else:
        flash('You are not authorized to perform this action.')
        return redirect(url_for('admin_dashboard'))


@app.route('/remove_song_fromadmin_album/<int:album_id>/<int:song_id>', methods=['POST'])
def remove_song_fromadmin_album(album_id, song_id):
    
    if 'username' in session and session['username'] == 'Tannu@gmail.com':
        album = album_creator.query.get(album_id)
        song = upload_song_creator.query.get(song_id)

        if album and song:
            album.songs.remove(song)
            db.session.commit()
            flash("Song removed from the album.")
        else:
            flash("Error: Album or song not found.")
    else:
        flash("You are not authorized to perform this action.")

    return redirect(url_for('admin_album', album_id=album_id))

@app.route('/deleteadmin_album/<int:album_id>', methods=['POST'])
def deleteadmin_album(album_id):
    if 'username' in session and session['username'] == 'Tannu@gmail.com':
        album = album_creator.query.get(album_id)

        if album:
            
            db.session.delete(album)
            db.session.commit()
            flash('Album deleted successfully!')
        else:
            flash('Album not found.')

        return redirect(url_for('admin_album'))
    else:
        flash('You are not authorized to perform this action.')
        return redirect(url_for('admin_dashboard'))

@app.route('/rate_song/<int:song_id>', methods=['POST'])
def rate_song(song_id):
    user = session.get('user')
    print("User:", user)

    if user is None:
        flash("You must be logged in to rate a song.")
        return redirect(url_for('login'))

    rating_value = request.form.get('rating')
    rating_value = int(rating_value)
    if 1 <= rating_value <= 5:
        try:
            existing_rating = Rating.query.filter_by(user_id=user['id'], song_id=song_id).first()
            if existing_rating:
                existing_rating.value = rating_value
            else:
                new_rating = Rating(value=rating_value, user_id=user['id'], song_id=song_id)
                db.session.add(new_rating)
            db.session.commit()
            flash("Rating updated successfully!")
        except IntegrityError as e:
            db.session.rollback()
            flash("Failed to rate the song.")
            print("Error:", e)

    return redirect(url_for('user_dashboard'))

@app.route('/all_creator', methods=['GET', 'POST'])
def all_creator():
    # Check if the user making the request is an admin
    if 'username' in session and session['username'] == 'Tannu@gmail.com':
        if request.method == 'POST':
            creator_id = request.form.get('creator_id')
            action = request.form.get('action') 

            creator = User.query.get(creator_id)
            if creator:
                print(f"Current Blacklisted Status: {creator.is_blacklisted}")

                if action == 'blacklist':
                    creator.is_blacklisted = True
                elif action == 'whitelist':
                    creator.is_blacklisted = False

                db.session.commit()

            else:
                print('User not found.')


        all_creators = User.query.filter_by(is_creator=True).all()

        return render_template('all_creator.html', all_creators=all_creators)
   

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)


        