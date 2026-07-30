from flask import Flask, render_template, request

app=Flask(__name__)
trips = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/trips", methods=["GET", "POST"])
def trips_page():

    if request.method== "POST":
        destination= request.form["destination"]
        date= request.form["date"]

        trips.append({
            "destination": destination,
            "date": date
        })
    
    return render_template("trips.html", trips=trips)

@app.route("/login")
def login():
    return render_template("login.html")


if __name__== "__main__":
    app.run(debug=True)

