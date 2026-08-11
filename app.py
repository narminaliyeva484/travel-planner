from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, date


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

    db = get_db_connection()

    trips = db.execute(
        "SELECT * FROM trips WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()

    trip_data = []

    for trip in trips:

        expenses = db.execute(
            "SELECT * FROM expenses WHERE trip_id = ?",
            (trip["id"],)
        ).fetchall()

        total_spent = sum(expense["amount"] for expense in expenses)

        start_date = datetime.strptime(trip["date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(trip["end_date"], "%Y-%m-%d").date()

        formatted_start_date = datetime.strptime(
            trip["date"], "%Y-%m-%d"
        ).strftime("%b %d")

        formatted_end_date = datetime.strptime(
            trip["end_date"], "%Y-%m-%d"
        ).strftime("%b %d")

        remaining_budget = trip["budget"] - total_spent
        today = date.today()


        if today < start_date:
            # Trip hasn't started yet
            days_remaining = (end_date - start_date).days + 1
            

        elif start_date <= today <= end_date:
            # Trip is currently happening
            days_remaining = (end_date - today).days + 1
            

        else:
            # Trip has already ended
            days_remaining = 0
    

        if days_remaining > 0:
            daily_allowance = remaining_budget / days_remaining
        else:
            daily_allowance = 0




        if trip["budget"] > 0:
            percentage_spent = (total_spent / trip["budget"]) * 100
        else:
            percentage_spent = 0

        trip_data.append({
            "trip": trip,
            "expenses": expenses,
            "total_spent": total_spent,
            "percentage_spent": percentage_spent,
            "daily_allowance": daily_allowance,
            "days_remaining": days_remaining,
            "remaining_budget": remaining_budget,
            "formatted_start_date": formatted_start_date,
            "formatted_end_date": formatted_end_date
        })

    db.close()

    return render_template("trips.html", trips=trip_data)


@app.route("/add-trip", methods=["GET","POST"])
def add_trip():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        destination = request.form["destination"]
        date = request.form["date"]
        end_date = request.form["end_date"]
        start = datetime.strptime(date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if end < start:
            flash("End date cannot be before the start date.")
            return redirect(url_for("add_trip"))
        
        budget = request.form["budget"]
        currency = request.form["currency"]

        db = get_db_connection()

        db.execute(
            "INSERT INTO trips (destination, date, end_date, budget, currency, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (destination, date, end_date, budget, currency, session["user_id"])
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
        end_date = request.form["end_date"]

        start = datetime.strptime(date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if end < start:
            flash("End date cannot be before the start date.")
            db.close()
            return redirect(url_for("edit_trip", trip_id=trip_id))

        db.execute("""UPDATE trips 
        SET destination = ?, date = ?, end_date = ? 
        WHERE id = ? AND user_id = ?
        """, 
        (destination, date, end_date, trip_id, session["user_id"]))

        db.commit()
        db.close()

        return redirect("/trips")

    trip = db.execute("SELECT * FROM trips WHERE id = ? AND user_id = ?", (trip_id,session["user_id"])).fetchone()

    db.close()

    return render_template("edit_trip.html", trip=trip)


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":
        username = request.form["username"].strip().lower()
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
        username = request.form["username"].strip().lower()
        password = request.form["password"]

        db = get_db_connection()

        user = db.execute(
            "SELECT * FROM users WHERE username = ?",( username, )
        ).fetchone()

        db.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect username or password.")
            return redirect(url_for("login"))
            

        session["user_id"]=user["id"]
        session["username"] = user["username"]

        return redirect(url_for("trips_page"))


    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("home"))


@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/edit-profile",methods =["GET","POST"])
def edit_profile():

    db=get_db_connection()

    if request.method == "POST":

        username = request.form["username"].strip().lower()
        email= request.form["email"]

        try:

            db.execute(
                "UPDATE users SET username = ?, email = ? WHERE id = ?",
                (username, email, session["user_id"])
            )

            db.commit()

            session["username"]= username

            db.close()

            return redirect(url_for("profile"))

        except sqlite3.IntegrityError:

            flash("Username or email already exists.")

            db.close()

            return redirect(url_for("edit_profile"))

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
        ).fetchone()

    db.close()

    return render_template("edit_profile.html", user=user) 


@app.route("/change-password",methods=["GET","POST"])
def change_password():

    db = get_db_connection()

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(user["password_hash"], current_password):
            db.close()
            flash("Current password is incorrect.")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            db.close()
            flash("New passwords do not match.")
            return redirect(url_for("change_password"))

        password_hash = generate_password_hash(new_password)

        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, session["user_id"])
        )

        db.commit()
        db.close()

        flash("Your password has been changed successfully.")
        return redirect(url_for("profile"))

    db.close()

    return render_template("change_password.html")


@app.route("/delete-account",methods=["GET","POST"])
def delete_account():

    db=get_db_connection()

    db.execute(
        "DELETE FROM trips WHERE user_id = ?",(session["user_id"],)
    )

    db.execute(
        "DELETE FROM users WHERE id = ?",
        (session["user_id"],)
    )

    db.commit()
    db.close()

    session.clear()

    return redirect(url_for("home"))



@app.route("/add-expense/<int:trip_id>", methods=["GET", "POST"])
def add_expense(trip_id):

    db = get_db_connection()

    trip = db.execute(
        "SELECT * FROM trips WHERE id = ? AND user_id = ?",
        (trip_id, session["user_id"])
    ).fetchone()

    if trip is None:
        db.close()
        return redirect(url_for("trips_page"))

    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        description = request.form["description"]
        date = request.form["date"]

        db.execute(
            """
            INSERT INTO expenses
            (trip_id, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (trip_id, amount, category, description, date)
        )

        db.commit()
        db.close()

        return redirect(url_for("trips_page"))

    db.close()

    return render_template(
        "add_expense.html",
        trip=trip
    )


@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):

    db = get_db_connection()

    expense = db.execute(
        """
        SELECT expenses.*
        FROM expenses
        JOIN trips ON expenses.trip_id = trips.id
        WHERE expenses.id = ? AND trips.user_id = ?
        """,
        (expense_id, session["user_id"])
    ).fetchone()

    if expense is None:
        db.close()
        return redirect(url_for("trips_page"))

    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        description = request.form["description"]
        date = request.form["date"]

        db.execute(
            """
            UPDATE expenses
            SET amount = ?, category = ?, description = ?, date = ?
            WHERE id = ?
            """,
            (amount, category, description, date, expense_id)
        )

        db.commit()
        db.close()

        return redirect(url_for("trips_page"))

    db.close()

    return render_template(
        "edit_expense.html",
        expense=expense
    )


@app.route("/delete-expense/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):

    db = get_db_connection()

    db.execute(
        """
        DELETE FROM expenses
        WHERE id = ?
        AND trip_id IN (
            SELECT id FROM trips WHERE user_id = ?
        )
        """,
        (expense_id, session["user_id"])
    )

    db.commit()
    db.close()

    return redirect(url_for("trips_page"))


if __name__== "__main__":
    app.run(debug=True)

