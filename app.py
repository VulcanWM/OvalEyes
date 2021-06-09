from flask import Flask, request, render_template, redirect
from string import printable
from werkzeug.security import check_password_hash
from functions import addcookie, getcookie, delcookie, makeaccount, getuser, gethashpass, verify, checkemailalready, checkusernamealready
import os
app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.config['SECRET_KEY'] = os.getenv("secretkey")

@app.route('/')
def index():
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    if getuser(getcookie("User"))['Verified'] == False:
      return render_template("error.html", error="Verify your account to access everything!")
    else:
      return render_template("index.html", user=getuser(getcookie("User")))

@app.route("/login")
def loginpage():
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    return render_template("error.html", error="You have already logged in!")

@app.route("/signup")
def signuppage():
  if getcookie("User") == False:
    return render_template("signup.html")
  else:
    return render_template("error.html", error="You have already logged in!")

@app.route("/signup", methods=['POST', 'GET'])
def signup():
  if request.method == 'POST':
    if getcookie("User") != False:
      return render_template("error.html", error="You have already logged in!")
    username = request.form['username']
    if len(username) > 25:
      return render_template("error.html", error="Your username cannot have more than 25 letters!")
    if len(username) < 2:
      return render_template("error.html", error="You have to have more than 2 letters in your username!")
    if set(username).difference(printable):
      return render_template("error.html", error="Your username cannot contain any special characters!")
    if username != username.lower():
      return render_template("error.html", error="Your username has to be all lowercase!")
    if checkusernamealready(username) == True:
      return render_template("error.html", error="A user already has this username! Try another one.")
    password = request.form['password']
    passworda = request.form['passwordagain']
    if password != passworda:
      return render_template("error.html", error="The two passwords don't match!")
    if len(password) > 25:
      return render_template("error.html", error="Your password cannot have more than 25 letters!")
    if len(password) < 2:
      return render_template("error.html", error="You have to have more than 2 letters in your password!")
    if set(password).difference(printable):
      return render_template("error.html", error="Your password cannot contain any special characters!")
    email = str(request.form['email']).lower()
    if checkusernamealready(email) == True:
      return render_template("error.html", error="A user already has this email! Try another one.")
    func = makeaccount(username, password, email)
    if func == True or func == None:
      addcookie("User", username)
      return render_template("success.html", success="Your account has been created! Check your emails to see a verification email so you can verify your account to do everything!")
    else:
      return render_template("error.html", error=func)

@app.route("/login", methods=['POST', 'GET'])
def login():
  if request.method == 'POST':
    if getcookie("User") != False:
      return render_template("error.html", error="You have already logged in!")
    username = request.form['username']
    if getuser(username) == False:
      return render_template("error.html", error="That is not a username!")
    password = request.form['password']
    if check_password_hash(gethashpass(username), password) == False:
      return render_template("error.html", error="Wrong password!")
    addcookie("User", username)
    return redirect("/")

@app.route("/verify/<username>/<id>")
def verifypage(username, id):
  func = verify(username, id)
  if func == True:
    return render_template("success.html", success="Your account has been verified!")
  else:
    return render_template("error.html", error="That is not a verification url!")

@app.route("/profile/<username>")
def profile(username):
  if getuser(username) == False:
    return render_template("error.html", error=f"{username} isn't a user!")
  else:
    return render_template("profile.html", user=getuser(username))