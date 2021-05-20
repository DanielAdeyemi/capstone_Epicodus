import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import StringField, TextAreaField, SubmitField, SelectField, FloatField
from wtforms.validators import InputRequired, DataRequired, Length

from helpers import apology, login_required

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"

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

class RaitingForm(FlaskForm):
  name = StringField("name", validators=[InputRequired("Name is required"), DataRequired("No empty tricks!"), Length(min=1, max=50, message="Name should be 1 to 50 characters long")])
  level= StringField("level", validators=[InputRequired("This field is required"), DataRequired("No empty tricks!"), Length(min=1, max=50, message="Level should be 2 to 50 characters long")])
  pc = FloatField("pc")
  mec = FloatField("mec")
  gm = FloatField("gm")
  com = FloatField("com")
  aty = FloatField("aty")
  gen = FloatField("gen")
  comments = TextAreaField("comments", validators=[InputRequired("Anything for this ref?"), DataRequired("No empty tricks!"), Length(min=5, max=200, message="Between 5 and 200 charachters")])
  submit=SubmitField("Rate him!")

class DeleteRefForm(FlaskForm):
  submit=SubmitField("Remove this ref")

@app.route("/")
# @login_required
def index():
  """Show rating of refs"""
  rating = db.execute("SELECT * FROM rank ORDER BY score DESC")
  deleteRefForm = DeleteRefForm()
  return render_template("index.html", rating=rating, deleteRefForm=deleteRefForm)


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
    if not check_password_hash(rows[0]["password"], request.form.get("password")):
      db.execute("UPDATE users SET password = ? WHERE user_id = ?", generate_password_hash(
                request.form.get("password")), session["user_id"])
      return redirect("/logout")
    return apology("New password is same as old one", 403)


@app.route("/rank", methods=["GET", "POST"])
@login_required
def rank():
  if request.method == "GET":
    return render_template("ranks.html")

  name = request.form.get("name")
  level = request.form.get("level")
  pc = float(request.form.get("pc"))
  mec = float(request.form.get("mec"))
  gm = float(request.form.get("gm"))
  com = float(request.form.get("com"))
  aty = float(request.form.get("aty"))
  gen = float(request.form.get("gen"))
  comments = request.form.get("comments")
  score = round(pc + mec + gm + com + aty + gen, 3)

  try:
    exist = db.execute("SELECT * FROM rank WHERE name = ?", name)[0]
    return redirect(url_for("edit_rank", ref_id=exist.id))
  except:
    exist = {}
  if exist == {}:
    new = db.execute("INSERT INTO rank(name, level, pc, mec, gm, com, atyp, gen, score, comments) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     name, level, pc, mec, gm, com, aty, gen, score, comments)
    return redirect(url_for("index"))
  

@app.route("/rank/<ref_id>/edit", methods=["GET", "POST"])
@login_required
def edit_rank(ref_id):
  ref = db.execute("SELECT * FROM rank WHERE id = ?", ref_id)[0]
  if request.method == "GET":
    return render_template("edit.html", ref=ref)
  
  level = request.form.get("level")
  pc = float(request.form.get("pc"))
  mec = float(request.form.get("mec"))
  gm = float(request.form.get("gm"))
  com = float(request.form.get("com"))
  aty = float(request.form.get("aty"))
  gen = float(request.form.get("gen"))
  comments = request.form.get("comments")
  score = round(pc + mec + gm + com + aty + gen, 3)

  pc_new = (ref['pc'] + pc) / 2
  mec_new = (ref['mec'] + mec) / 2
  gm_new = (ref['gm'] + gm) / 2
  com_new = (ref['com'] + com) / 2
  atyp_new = (ref['atyp'] + aty) / 2
  gen_new = (ref['gen'] + gen) / 2
  score_new = round((ref['score'] + score) / 2, 3)
  comments_old = ref['comments']
  comments_new = comments_old + "/r" + comments
  db.execute("UPDATE rank SET level = ?, pc = ?, mec = ?, gm = ?, com = ?, atyp = ?, gen = ?, score = ?, comments = ?  WHERE id = ?",
            level, pc_new, mec_new, gm_new, com_new, atyp_new, gen_new, score_new, comments_new, ref_id)

  return redirect(url_for("index"))

@app.route("/rank/<ref_id>/comments")
@login_required
def comments(ref_id):
  ref = db.execute("SELECT comments FROM rank WHERE id = ?", ref_id)
  
  return render_template("comments.html",refs=ref)

@app.route("/ref/<ref_id>/delete", methods=["POST"])
@login_required
def delete_ref(ref_id):
  db.execute("DELETE FROM rank WHERE id = ?", (ref_id))
  return redirect(url_for("index"))

def errorhandler(e):
  """Handle error"""
  if not isinstance(e, HTTPException):
    e = InternalServerError()
  return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
  app.errorhandler(code)(errorhandler)
