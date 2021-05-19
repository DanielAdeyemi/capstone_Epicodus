import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
  response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  response.headers["Expires"] = 0
  response.headers["Pragma"] = "no-cache"
  return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///refs.db")


@app.route("/")
@login_required
def index():
  """Show rating of refs"""
  return render_template("sorry.html", message="TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
  """Log user in"""

  # Forget any user_id
  session.clear()

  # User reached route via POST (as by submitting a form via POST)
  if request.method == "POST":

    # Ensure username was submitted
    if not request.form.get("username"):
      return render_template("sorry.html", message="Please, provide username")

    # Ensure password was submitted
    elif not request.form.get("password"):
      return render_template("sorry.html", message="Please, provide password")

    # Query database for username
    rows = db.execute("SELECT * FROM users WHERE username = :username",
                      username=request.form.get("username"))

    # Ensure username exists and password is correct
    if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
      return render_template("sorry.html", message="Wrong username or password")

    # Remember which user has logged in
    session["user_id"] = rows[0]["user_id"]

    # Redirect user to home page
    return redirect("/")

  # User reached route via GET (as by clicking a link or via redirect)
  else:
    return render_template("login.html")


@app.route("/logout")
def logout():
  """Log user out"""

  # Forget any user_id
  session.clear()

  # Redirect user to login form
  return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
  """Register user"""
  if request.method == "GET":
    return render_template("register.html")
  else:
    if not request.form.get("username"):
      return render_template("sorry.html", message="Please, provide username")
    # Ensure password was submitted
    elif not request.form.get("password"):
      return render_template("sorry.html", message="Please, provide password")
    elif (request.form.get("password") != request.form.get("password_2")):
      return render_template("sorry.html", message="Passwords don't match")
    rows = db.execute("SELECT * FROM users WHERE username = :username",
                      username=request.form.get("username"))
    # Ensure username doen't exists
    if len(rows) == 1:
      return render_template("sorry.html", message="This username already exists")
    else:
      db.execute("INSERT INTO users(username, password) VALUES(?, ?)", request.form.get(
                "username"), generate_password_hash(request.form.get("password")))
      return redirect("/login")


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
  if request.method == "GET":
    return render_template("change.html")
  else:
    if not request.form.get("old"):
      return apology("Please, provide old password", 403)
    elif not request.form.get("password"):
      return apology("Provide new password", 403)
    elif not request.form.get("password_2"):
      return apology("Confirm new password", 403)
    elif request.form.get("password") != request.form.get("password_2"):
      return apology("Passwords don't match", 403)

    rows = db.execute("SELECT * FROM users WHERE user_id = ?",
                      session["user_id"])
    if not check_password_hash(rows[0]["password"], request.form.get("old")):
      return apology("Old password incorrect", 403)
    if not check_password_hash(rows[0]["hash"], request.form.get("password")):
      db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(
                request.form.get("password")), session["user_id"])
      return redirect("/logout")
    return apology("New password is same as old one", 403)
