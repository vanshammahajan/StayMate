from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"


def initialize_db():
    with sqlite3.connect('roomier.db') as conn:
        cur = conn.cursor()

        # Create users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                dob DATE,
                email TEXT UNIQUE,
                password TEXT NOT NULL
            )
        ''')

        # Create preference table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS preference (
                user_id INTEGER PRIMARY KEY,
                city varchar(50),
                same_hometown TEXT,
                non_veg_roommate TEXT,
                smoke TEXT,
                alcohol TEXT,
                religion_preference TEXT,
                daily_rhythm TEXT,
                social_personality TEXT,
                loud_music TEXT,
                split_groceries TEXT,
                chores TEXT,
                cleaning_preference TEXT,
                noise_tolerance TEXT,
                pets TEXT,
                overnight_guests TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS room (
                      title VARCHAR(50),
                      description VARCHAR(50),
                      rent INT,
                      address VARCHAR(50),
                      rooms INT,
                      city VARCHAR(50)  
                    )
                ''')
        conn.commit()


initialize_db()


# Registration Form Page
@app.route("/register", methods=["GET"])
def register_form():
    return render_template("registration.html")


# Registration Form Submission
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    name = request.form.get("name")
    dob = request.form.get("dob")

    try:
        with sqlite3.connect('roomier.db') as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (full_name, email, password, dob) VALUES (?, ?, ?, ?)",
                        (name, username, password, dob))
            conn.commit()
        return redirect(url_for("login_form"))
    except sqlite3.IntegrityError:
        return "Email already exists", 400


# Login Page
@app.route('/', methods=["GET"])
def login_form():
    return render_template("login.html")


# Login Form Submission
@app.route('/', methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    try:
        with sqlite3.connect('roomier.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name, password FROM users WHERE email = ?", (username,))
            result = cursor.fetchone()

        if result is None:
            return "Invalid email", 401

        user_id, name, stored_password = result
        if password != stored_password:
            return "Wrong password", 403

        session["user_id"] = user_id
        session["email"] = username
        session["name"] = name
    
        cursor.execute("SELECT 1 FROM preference WHERE user_id = ?", (user_id,))
        has_pref = cursor.fetchone()
        if has_pref:
            return redirect(url_for("home"))
        else:
            return redirect(url_for("preference_form"))
    
    except Exception as e:
        return str(e), 500


# Preference Form Page
@app.route('/preference', methods=["GET"])
def preference_form():
    return render_template("preference.html")


# Preference Form Submission
@app.route('/preference', methods=["POST"])
def preference():
    if "user_id" not in session:
        return redirect(url_for("login_form"))

    user_id = session["user_id"]

    # Collect preferences from the form
    city = request.form.get("city")
    same_hometown = request.form.get("sameHometown")
    non_veg_roommate = request.form.get("nonVegRoommate")
    smoke = request.form.get("smoke")
    alcohol = request.form.get("alcohol")
    religion_preference = request.form.get("religionPreference")
    daily_rhythm = request.form.get("dailyRhythm")
    social_personality = request.form.get("socialPersonality")
    loud_music = request.form.get("loudMusic")
    split_groceries = request.form.get("splitGroceries")
    chores = request.form.get("chores")
    cleaning_preference = request.form.get("cleaningPreference")
    noise_tolerance = request.form.get("noiseTolerance")
    pets = request.form.get("pets")
    overnight_guests = request.form.get("overnightGuests")

    try:
        with sqlite3.connect('roomier.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO preference (
                    user_id, city, same_hometown, non_veg_roommate, smoke, alcohol, religion_preference, 
                    daily_rhythm, social_personality, loud_music, split_groceries, chores, 
                    cleaning_preference, noise_tolerance, pets, overnight_guests
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
            ''', (
                user_id, city, same_hometown, non_veg_roommate, smoke, alcohol, religion_preference,
                daily_rhythm, social_personality, loud_music, split_groceries, chores,
                cleaning_preference, noise_tolerance, pets, overnight_guests
            ))
            conn.commit()
        return redirect(url_for("home"))
    except Exception as e:
        return f"An error occurred: {e}"


# Home Page after preferences submitted (can update as needed)
@app.route('/home', methods=["GET"])
def home():
    if "user_id" not in session:
        return redirect(url_for("login_form"))

    return render_template("home.html")


# Find Match Form Page
@app.route('/find', methods=["GET"])
def find_form():
    if "user_id" not in session:
        return redirect(url_for("login_form"))

    return render_template("find.html")


# Find Match Action (placeholder)
@app.route('/find', methods=["POST"])
def find():
    if "user_id" not in session:
        return redirect(url_for("login_form"))
    city = request.form.get("city")
    session['city'] = city
    return redirect(url_for("result"))


# Result Page (placeholder)
@app.route('/result', methods=["GET"])
def result():
    if "user_id" not in session:
        return redirect(url_for("login_form"))

    d = {}
    city = session.get("city")
    user = session["user_id"]

    try:
        with sqlite3.connect('roomier.db') as conn:
            cursor = conn.cursor()

            # Get the current user's preferences
            cursor.execute('''
                SELECT * 
                FROM preference 
                WHERE user_id = ?
            ''', (user,))
            current_user_prefs = cursor.fetchone()

            if not current_user_prefs:
                return "Current user preferences not found."

            # Get all users from the given city (assuming city is stored in 'city' column)
            cursor.execute('''
                SELECT * 
                FROM preference 
                WHERE city = ? AND user_id != ?
            ''', (city, user))
            matches = cursor.fetchall()

            for match in matches:
                match_user_id = match[0]  # assuming user_id is the first column
                count = 0

                # Compare each attribute (skip user_id and email if needed)
                for i in range(len(current_user_prefs)):
                    if i == 0:  # skip user_id
                        continue
                    if current_user_prefs[i] == match[i]:
                        count += 1

                score = (count / (len(current_user_prefs) - 1)) * 100  # -1 to skip user_id
                d[match_user_id] = round(score, 2)

            conn.commit()

    except Exception as e:
        return f"An error occurred: {e}"

    return render_template("result.html", data=d)


@app.route('/room', methods=["GET"])
def room_option():
    return render_template("room.html")


@app.route('/room/register', methods=["GET"])
def room_fform():
    return render_template("roomregister.html")


@app.route('/room/register', methods=["POST"])
def room_register():
    city = request.form.get("city")
    description = request.form.get("description")
    rent = request.form.get("rent")
    address = request.form.get("address")
    room = request.form.get("rooms")
    title = request.form.get("title")
    try:
        with sqlite3.connect('roomier.db') as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO room (title, description, rent, address, rooms, city) VALUES (?, ?, ?, ?, ?, ?)",
                        (title, description, rent, address, room, city))
            conn.commit()
        return redirect(url_for("home"))
    except sqlite3.IntegrityError:
        return "Unknown Error", 400


@app.route('/room/find', methods=["GET"])
def room_sform():
    return render_template("roomfind.html")


@app.route('/room/find', methods=["POST"])
def room_search():
    city = request.form.get("city")
    try:
        with sqlite3.connect('roomier.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT title, address, rooms, description, rent, city FROM room WHERE city = ?", (city,))
            rooms = cur.fetchall()  # List of tuples
        return render_template("roomresults.html", rooms=rooms, city=city)
    except sqlite3.IntegrityError:
        return "Unknown Error", 400


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_form"))


if __name__ == '__main__':
    app.run(debug=True)
