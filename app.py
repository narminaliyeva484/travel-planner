from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3


app=Flask(__name__)
app.secret_key = "your-secret-key-here"

def get_db_connection():
    conn= sqlite3.connect("travel_planner.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/trips", methods=["GET", "POST"])
def trips_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db= get_db_connection()

    trips = db.execute(
        "SELECT * FROM trips WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()

    db.close()

    return render_template("trips.html", trips=trips)


@app.route("/add-trip", methods=["GET","POST"])
def add_trip():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        destination = request.form["destination"]
        date = request.form["date"]

        db = get_db_connection()

        db.execute(
            "INSERT INTO trips (destination, date, user_id) VALUES (?, ?, ?)",
            (destination, date, session["user_id"])
        )

        db.commit()
        db.close()

        return redirect("/trips")

    return render_template("add_trip.html")

@app.route("/delete/<int:trip_id>", methods=["POST"])
def delete_trip(trip_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()

    db.execute(
        "DELETE FROM trips WHERE id = ? AND user_id = ?",
        (trip_id,session["user_id"])
    )

    db.commit()
    db.close()

    return redirect(url_for("trips_page"))


@app.route("/edit/<int:trip_id>" , methods=["GET", "POST"])
def edit_trip(trip_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    db= get_db_connection()

    if request.method=="POST":

        destination= request.form["destination"]
        date= request.form["date"]

        db.execute("UPDATE trips SET destination = ? , date = ? WHERE id = ? AND user_id = ?", (destination, date, trip_id, session["user_id"]))

        db.commit()
        db.close()

        return redirect("/trips")

    trip = db.execute("SELECT * FROM trips WHERE id = ? AND user_id = ?", (trip_id,session["user_id"])).fetchone()

    db.close()

    return render_template("edit_trip.html", trip=trip)


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        db= get_db_connection()
        
        try:

            db.execute(
                "INSERT INTO users (username,email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
                )

            db.commit()
            db.close()

        except sqlite3.IntegrityError:
            flash("Username or email already exists.")

            db.close()

            return redirect(url_for("register"))

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods =["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()

        user = db.execute(
            "SELECT * FROM users WHERE username = ?",( username, )
        ).fetchone()

        db.close()

        if user is None:
            return "User not found"

        if not check_password_hash(user["password_hash"], password):
            return "Incorrect password"

        session["user_id"]=user["id"]
        session["username"] = user["username"]

        return redirect(url_for("trips_page"))


    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("home"))



if __name__== "__main__":
    app.run(debug=True)

