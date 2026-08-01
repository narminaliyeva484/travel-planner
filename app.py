from flask import Flask, render_template, request
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

    if request.method == "POST":
        destination= request.form["destination"]
        date= request.form["date"]

        db= get_db_connection()

        db.execute(
            "INSERT INTO trips (destination, date) VALUES (?, ?)", (destination, date)
        )

        db.commit()
        db.close()

    db= get_db_connection()
    
    trips = db.execute(
        "SELECT * FROM trips"
    ).fetchall()

    db.close()

    return render_template("trips.html", trips=trips)

@app.route("/login")
def login():
    return render_template("login.html")


if __name__== "__main__":
    app.run(debug=True)

