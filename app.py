from flask import Flask, request, render_template, redirect, send_file, Response
from string import printable
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functions import addcookie, getcookie, delcookie, makeaccount, getuser, gethashpass, verify, checkemailalready, checkusernamealready, adddesc, follow, unfollow, getnotifs, clearnotifs, allseen, makepost, getpost, getpostid, viewpost, delpost, getsettings, changepublicsettings, changeemailsettings, acceptfr, addnotif, declinefr, allfrs, alluserposts, is_human, editpost, send_mail, likepost, unlikepost, getcomment, comment
from functions import mods
import os
app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.config['SECRET_KEY'] = os.getenv("secretkey")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage.pfps'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
pfps = SQLAlchemy(app)

UPLOAD_FOLDER = './pfps'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class Img(pfps.Model):
  id = pfps.Column(pfps.Integer, primary_key=True)
  img = pfps.Column(pfps.Text, nullable=False)
  mimetype = pfps.Column(pfps.Text, nullable=False)

pfps.create_all()

@app.route('/')
def index():
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    if getuser(getcookie("User"))['Verified'] == False:
      return render_template("error.html", error="Verify your account to access everything!")
    else:
      return render_template("index.html", user=getuser(getcookie("User")), number=len(getnotifs(getcookie("User"))))

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
    if checkemailalready(email) == True:
      return render_template("error.html", error="A user already has this email! Try another one.")
    captcha_response = request.form.get("g-recaptcha-response")
    if is_human(captcha_response):
      pass
    else:
      return render_template("error.html", error="No bots allowed!")
    func = makeaccount(username, password, email)
    if func == True or func == None:
      addcookie("User", username)
      return render_template("success.html", success="Your account has been created! Check your emails to see a verification email so you can verify your account to do everything!")
    else:
      return render_template("error.html", error=f"{func} Account not created! Try again.")

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
  username = username.lower()
  if getuser(username) == False:
    return render_template("error.html", error=f"{username} isn't a user!")
  else:
    follow = False
    if getcookie("User") == False:
      follow = False
    else:
      if getcookie("User") == username:
        follow = "NO"
      elif getcookie("User") in getuser(username)['Followers']:
        follow = True
      else:
        follow = False
    return render_template("profile.html", user=getuser(username), follow=follow)

@app.route("/adddesc")
def adddescpage():
  if getcookie("User") == False:
    return render_template("error.html", error="You are not logged in!")
  else:
    if getuser(getcookie("User"))['Verified'] == False:
      return render_template("error.html", error="Verify your account to access everything!")
    desc = getuser(getcookie("User"))['Description']
    if desc == None:
      desc = ""
    return render_template("adddesc.html", desc=desc)

@app.route("/adddesc", methods=['POST', 'GET'])
def adddescfunc():
  if request.method == 'POST':
    if getcookie("User") != False:
      if getuser(getcookie("User"))['Verified'] == False:
        return render_template("error.html", error="Verify your account to access everything!")
      desc = request.form['desc']
      if len(desc) > 150:
        return render_template("error.html", error="Your description has to be less than 150 characters!")
      func = adddesc(getcookie("User"), desc)
      if func == True:
        return redirect(f"/profile/{getcookie('User')}")
      else:
        return render_template("error.html", error=func)
    else:
      return render_template("error.html", error="You are not logged in!")

@app.route("/followers/<username>")
def followers(username):
  if getcookie("User") == False:
    return render_template("error.html", error="You need to log in to see a user's followers!")
  else:
    if getuser(getcookie("User"))['Verified'] == False:
      return render_template("error.html", error="Verify your account to access everything!")
    user = getuser(username)
    return render_template("follow.html", name="Followers", user=user, msg=f"{username} has no followers!")

@app.route("/following/<username>")
def following(username):
  if getcookie("User") == False:
    return render_template("error.html", error="You need to log in to see who a user is following!")
  else:
    if getuser(getcookie("User"))['Verified'] == False:
      return render_template("error.html", error="Verify your account to access everything!")
    user = getuser(username)
    return render_template("follow.html", name="Following", user=user, msg=f"{username} is not following anyone!")

@app.route("/addpfp")
def addpfppage():
  if getcookie("User") == False:
    return render_template("error.html", error="You haven't logged in!")
  else:
    if getuser(getcookie("User"))['Verified'] == False:
      return render_template("error.html", error="Verify your account to access everything!")
    return render_template("addpfp.html")

@app.route('/addpfp', methods=['GET', 'POST'])
def addpfp():
  if request.method == 'POST':
    if getcookie("User") == False:
      return render_template("error.html", error="You haven't logged in!")
    else:
      if getuser(getcookie("User"))['Verified'] == False:
        return render_template("error.html", error="Verify your account to access everything!")
      file1 = request.files['image']
      mimetype = file1.mimetype
      img = Img(img=file1.read(), mimetype=mimetype, id=getuser(getcookie("User"))['_id'])
      pfps.session.add(img)
      pfps.session.commit()
      return redirect("/")

@app.route("/pfps/<username>")
def pfpuser(username):
  try:
    theid = getuser(username)['_id']
    img = Img.query.filter_by(id=theid).first()
    return Response(img.img, mimetype=img.mimetype)
  except:
    return send_file("static/unnamed.png")

@app.route("/follow/<username>")
def followpage(username):
  if getcookie("User") == False:
    return render_template("error.html", error="You haven't logged in!")
  if getuser(getcookie("User"))['Verified'] == False:
    return render_template("error.html", error="Verify your account to access everything!")
  if getuser(username)['Verified'] == False:
    return render_template("error.html", error=f"{username} isn't verified!")
  func = follow(getcookie("User"), username)
  if func == True:
    return redirect(f"/profile/{username}")
  else:
    return render_template("error.html", error=func)

@app.route("/unfollow/<username>")
def unfollowpage(username):
  if getcookie("User") == False:
    return render_template("error.html", error="You haven't logged in!")
  if getuser(getcookie("User"))['Verified'] == False:
    return render_template("error.html", error="Verify your account to access everything!")
  func = unfollow(getcookie("User"), username)
  if func == True:
    return redirect(f"/profile/{username}")
  else:
    return render_template("error.html", error=func)

@app.route("/notifs")
def notifs():
  if getcookie("User") == False:
    return render_template("login.html")
  if getuser(getcookie("User")) == False:
    delcookie("hello")
    return redirect("/")
  notifs = getnotifs(getcookie("User"))
  allseen(getcookie("User"))
  return render_template("notifs.html", notifs=notifs)

@app.route("/clearnotifs")
def clearnotifsapp():
  if getcookie("User") == False:
    return render_template("login.html")
  if getuser(getcookie("User")) == False:
    delcookie("hello")
    return redirect("/")
  clearnotifs(getcookie("User"))
  return redirect("/notifs")

@app.route("/makepost")
def makepostpage():
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    if getuser(getcookie("User"))['Verified'] == False:
      return render_template("error.html", error="Verify your account to access everything!")
    return render_template("makepost.html")

@app.route("/makepost", methods=['GET', 'POST'])
def makepostfunc():
  if request.method == 'POST':
    if getcookie("User") == False:
      return render_template("login.html")
    else:
      if getuser(getcookie("User"))['Verified'] == False:
        return render_template("error.html", error="Verify your account to access everything!")
      username = getcookie("User")
      title = request.form['title']
      desc = request.form['desc']
      posttype = request.form['posttype']
      if getpost(desc) != False:
        return render_template("error.html", error="You already have a post with the same description!")
      if len(desc) > 300:
        return render_template("error.html", error="You cannot have more than 300 letters!")
      makepost(username, title, desc, posttype)
      theid = str(getpost(desc)['_id'])
      return redirect(f"/post/{theid}")

@app.route("/post/<theid>")
def post(theid):
  if getpostid(int(theid)) == False:
    return render_template("error.html", "This post doesn't exist!")
  post = getpostid(int(theid))
  comments = getcomment(int(theid))
  if post['Type'] == 'Public':
    perms = {"perms": False, "liked": False}
    if getcookie("User") == False:
      pass
    else:
      viewpost(theid, getcookie("User"))
      if post['Author'] == getcookie("User"):
        del perms['perms']
        perms['perms'] = True
      elif getcookie("User") in mods:
        del perms['perms']
        perms['perms'] = True
      if getcookie("User") in post['LikesPeople']:
        del perms['liked']
        perms['liked'] = True
    return render_template("post.html", post=post, perms=perms['perms'], liked=perms['liked'], comments=comments)
  else:
    if getcookie("User") in post['LikesPeople']:
      del perms['liked']
      perms['liked'] = True
    if getcookie("User") in mods:
      return render_template("post.html", post=post, perms=True, liked=perms['liked'], comments=comments)
    elif getcookie("User") == post['Author']:
      return render_template("post.html", post=post, perms=True, liked=perms['liked'], comments=comments)
    elif getcookie("User") in getuser(post['Author'])['Followers']:
      return render_template("post.html", post=post, perms=False, liked=perms['liked'], comments=comments)
    else:
      return render_template("error.html", error=f"You cannot view this private post unless you are following {post['Author']}!")

@app.route("/deletepost/<theid>")
def deletepost(theid):
  if getpostid(int(theid)) == False:
    return render_template("error.html", error="This post isn't a post!")
  title = getpostid(int(theid))['Title']
  if getcookie("User") == False:
    return render_template("error.html", error="You aren't logged in!")
  func = delpost(getcookie("User"), int(theid))
  if func == True:
    return render_template("success.html", success=f"The post {title} has been deleted!")
  else:
    return render_template("error.html", error=func)

@app.route("/settings")
def settings():
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    return render_template("settings.html", settings=getsettings(getcookie("User")))

@app.route("/settings/public")
def settingspublic():
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    func = changepublicsettings(getcookie("User"))
    if func == True:
      return redirect("/settings")
    else:
      return render_template("error.html", error="Something unexpected happened!")

@app.route("/settings/emailnotif")
def settingemailnotif():
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    func = changeemailsettings(getcookie("User"))
    if func == True:
      return redirect("/settings")
    else:
      return render_template("error.html", error="Something unexpected happened!")

@app.route("/accept/<follower>/<following>")
def acceptfrpage(follower, following):
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    func = acceptfr(getcookie("User"), follower, following)
    if func == True:
      return render_template("success.html", success=f"You accepted a follow request from {follower}!")
      addnotif(follower, f"{following} accepted a follow request from you!")
    else:
      return render_template("error.html", error=func)

@app.route("/decline/<follower>/<following>")
def declinefrpage(follower, following):
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    func = declinefr(getcookie("User"), follower, following)
    if func == True:
      return render_template("success.html", success=f"You declined a follow request from {follower}!")
      addnotif(follower, f"{following} declined a follow request from you!")
    else:
      return render_template("error.html", error=func)

@app.route("/allfrs")
def frs():
  if getcookie("User") == False:
    return render_template("login.html")
  else:
    if getsettings(getcookie("User"))['Public'] == True:
      return render_template("error.html", error="You can't have follow requests if your account is public!")
    else:
      return render_template("frs.html", allfr=allfrs(getcookie("User")))

@app.route("/posts/<username>")
def usersposts(username):
  username = username.lower()
  if getuser(username) == False:
    return render_template("error.html", error=f"{username} isn't a user!")
  else:
    posts = alluserposts(username)
    return render_template("posts.html", 
    posts=posts, title=f"{username.upper()}'S POSTS", username=username)

@app.route("/editpost/<theid>")
def editpostpage(theid):
  if getcookie("User") == False:
    return render_template("error.html", error="You are not logged in!")
  if getpostid(int(theid)) == False:
    return render_template("error.html", error="This post isn't a post!")
  post = getpostid(int(theid))
  username = getcookie("User")
  if post['Author'] == username:
    pass
  elif username in mods:
    pass
  else:
    return render_template("error.html", error="You cannot edit this post!")
  return render_template("editpost.html", desc=post['Description'], theid=theid)

@app.route("/editpostfunc/<theid>", methods=['POST', 'GET'])
def editpostfunc(theid):
  if request.method == 'POST':
    if getcookie("User") == False:
      return render_template("error.html", error="You are not logged in!")
    if getpostid(int(theid)) == False:
      return render_template("error.html", error="This post isn't a post!")
    desc = request.form['desc']
    func = editpost(getcookie("User"), int(theid), desc)
    if func == True:
      return redirect(f"/post/{theid}")
    else:
      return render_template("error.html", error=func)

@app.route("/resendverification")
def resendverification():
  if getcookie("User") == False:
    return render_template("error.html", error="You are not logged in!")
  user = getuser(getcookie("User"))
  if user['Verified'] == True:
    return render_template("error.html", error="You have already verified your email!")
  func = send_mail(user['Email'], user['Username'], user['_id'])
  if func == True:
    return render_template("sucesss.html", success="Email verification sent! Check your email.")
  else:
    return render_template("error.html", error=func)

@app.route("/likepost/<theid>")
def likepostpage(theid):
  if getcookie("User") == False:
    return render_template("error.html", error="You are not logged in!")
  func = likepost(theid, getcookie("User"))
  if func == True:
    return redirect(f"/post/{theid}")
  else:
    return render_template("error.html", error=func)

@app.route("/unlikepost/<theid>")
def unlikepostpage(theid):
  if getcookie("User") == False:
    return render_template("error.html", error="You are not logged in!")
  func = unlikepost(theid, getcookie("User"))
  if func == True:
    return redirect(f"/post/{theid}")
  else:
    return render_template("error.html", error=func)

@app.route("/commentpage/<postid>", methods=['POST', 'GET'])
def commentpage(postid):
  if request.method == 'POST':
    if getcookie("User") == False:
      return render_template("error.html", error="You are not logged in!")
    thecomment = request.form['comment']
    func = comment(getcookie("User"), int(postid), thecomment)
    if type(func) is str:
      return render_template("error.html", error=func)
    else:
      return redirect(func[0])