from flask import Flask, render_template, request, redirect, url_for
import sqlite3


app=Flask(__name__)

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

    db= get_db_connection()

    trips = db.execute(
        "SELECT * FROM trips"
    ).fetchall()

    db.close()

    return render_template("trips.html", trips=trips)


@app.route("/add-trip", methods=["GET","POST"])
def add_trip():

    if request.method == "POST":

        destination = request.form["destination"]
        date = request.form["date"]

        db = get_db_connection()

        db.execute(
            "INSERT INTO trips (destination, date) VALUES (?, ?)",
            (destination, date)
        )

        db.commit()
        db.close()

        return redirect("/trips")

    return render_template("add_trip.html")

@app.route("/delete/<int:trip_id>", methods=["POST"])
def delete_trip(trip_id):
    db = get_db_connection()

    db.execute(
        "DELETE FROM trips WHERE id = ?",
        (trip_id,)
    )

    db.commit()
    db.close()

    return redirect(url_for("trips_page"))


@app.route("/edit/<int:trip_id>" , methods=["GET", "POST"])
def edit_trip(trip_id):
    db= get_db_connection()

    if request.method=="POST":

        destination= request.form["destination"]
        date= request.form["date"]

        db.execute("UPDATE trips SET destination = ? , date = ? WHERE id = ?", (destination, date, trip_id))

        db.commit()
        db.close()

        return redirect("/trips")

    trip = db.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()

    db.close()

    return render_template("edit_trip.html", trip=trip)


@app.route("/login")
def login():
    return render_template("login.html")




if __name__== "__main__":
    app.run(debug=True)

