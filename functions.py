import pymongo
import smtplib
import ssl
import random
import requests
import json
from flask import session
import os
import dns
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
client = pymongo.MongoClient(os.getenv("clientm"))
usersdb = client.Users
profilescol = usersdb.Profiles
notifscol = usersdb.Notifications
settingscol = usersdb.Settings
frcol = usersdb.FollowRequests
postsdb = client.Posts
postscol = postsdb.Posts
mods = ["vulcanwm", "ruiwenge2"]
def addcookie(key, value):
  session[key] = value

def delcookie(keyname):
  session.clear()

def getcookie(key):
  try:
    if (x := session.get(key)):
      return x
    else:
      return False
  except:
    return False


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)

def makeaccount(username, password, email):
  passhash = generate_password_hash(password)
  id = random_with_N_digits(10)
  while getuserid(int(id)) == True:
    id = random_with_N_digits(10)
  document = [{
    "_id": int(id),
    "Username": username,
    "Password": passhash,
    "Likes": 0,
    "Created": str(datetime.datetime.now()),
    "PFP": None,
    "Email": email,
    "Verified": False,
    "Blocked": [],
    "Followers": [],
    "Following": [],
    "Description": None
  }]
  func = send_mail(email, username, id)
  if func == True:
    profilescol.insert_many(document)
  else:
    return func

def gethashpass(username):
  myquery = { "Username": username }
  mydoc = profilescol.find(myquery)
  for x in mydoc:
    return x['Password']
  return False

def getuserid(id):
  myquery = { "_id": int(id) }
  mydoc = profilescol.find(myquery)
  for x in mydoc:
    return True
  return False

def getuser(username):
  myquery = { "Username": username }
  mydoc = profilescol.find(myquery)
  for x in mydoc:
    if x.get("Deleted", None) == None:
      return x
    return False
  return False

def checkusernamealready(username):
  myquery = { "Username": username }
  mydoc = profilescol.find(myquery)
  for x in mydoc:
    return True
  return False

def checkemailalready(email):
  myquery = { "Email": email }
  mydoc = profilescol.find(myquery)
  for x in mydoc:
    return True
  return False

def verify(username, id):
  user = getuser(username)
  if user == False:
    return False
  userid = str(user['_id'])
  if str(userid) == str(id):
    user2 = user
    del user2['Verified']
    user2['Verified'] = True
    delete = {"Username": username}
    profilescol.delete_one(delete)
    profilescol.insert_many([user2])
    return True
  else:
    return False

def send_mail(usermail, username, id):  
    context = ssl.create_default_context()
    MAILPASS = os.getenv("MAIL_PASSWORD")
    html = f"""
    <h1>Hello {username}!</h1>
    <p><strong>You have signed up for an account in OvalEyes!</strong></p>
    <p>Click <a href='https://OvalEyes.VulcanWM.repl.co/verify/{username}/{str(id)}'>here</a> to verify your account</p>
    <p>If you didn't make this account, reply back to this email saying this isn't your account and <strong>DO NOT</strong> click on the link or the user who made the account will get verified with your email!</p>
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = "OvalEyes Verification Email"
    part2 = MIMEText(html, "html")
    message.attach(part2)
    try:
      sendermail = "ovaleyesofficial@gmail.com"
      password = MAILPASS
      gmail_server = smtplib.SMTP('smtp.gmail.com', 587)
      gmail_server.starttls(context=context)
      gmail_server.login(sendermail, password)
      message["From"] = sendermail
      message["To"] = usermail
      gmail_server.sendmail(sendermail, usermail, message.as_string())
      return True
    except Exception as e:
      return "Verification email not sent, due to some issues."
      gmail_server.quit()

def adddesc(username, desc):
  try: 
    user = getuser(username)
    del user['Description']
    user['Description'] = desc
    delete = {"Username": username}
    profilescol.delete_one(delete)
    profilescol.insert_many([user])
    return True
  except Exception as e: 
    return e

def follow(follower, following):
  follower = follower.lower()
  following = following.lower()
  if follower in getuser(following)['Followers']:
    return f'You are already following {following}!'
  if getuser(following) == False:
    return f"{following} is not a real user!"
  if follower == following:
    return "You can't follow yourself!"
  if getsettings(following)['Public'] == False:
    if checkfr(follower, following) != False:
      return f"You are waiting for {following} to accept your follow request!"
    followrequest(follower, following)
    return True
  followeruser = getuser(follower)
  followingdoc = followeruser['Following']
  followingdoc.append(following)
  del followeruser['Following']
  followeruser['Following'] = followingdoc
  delete = {"Username": follower}
  profilescol.delete_one(delete)
  profilescol.insert_many([followeruser])
  followinguser = getuser(following)
  followersdoc = followeruser['Followers']
  followersdoc.append(follower)
  del followinguser['Followers']
  followinguser['Followers'] = followersdoc
  delete = {"Username": following}
  profilescol.delete_one(delete)
  profilescol.insert_many([followinguser])
  return True

def unfollow(username, unfollowing):
  if username not in getuser(unfollowing)['Followers']:
    return f'You are not following {unfollowing}!'
  if getuser(unfollowing) == False:
    return f"{unfollowing} is not a real user!"
  user = getuser(username)
  doc = user['Following']
  doc.remove(unfollowing)
  del user['Following']
  user['Following'] = doc
  delete = {"Username": username}
  profilescol.delete_one(delete)
  profilescol.insert_many([user])
  other = getuser(unfollowing)
  otherdoc = other['Followers']
  otherdoc.remove(username)
  del other['Followers']
  other['Followers'] = otherdoc
  otherdelete = {"Username": unfollowing}
  profilescol.delete_one(otherdelete)
  profilescol.insert_many([other])
  return True

def getnotifs(username):
  myquery = { "Username": username }
  mydoc = notifscol.find(myquery)
  notifs = []
  for x in mydoc:
    notifs.append(x)
  return notifs

def addnotif(username, notif):
  notifdoc = {"Username": username, "Notification": notif, "Seen": False}
  notifscol.insert_many([notifdoc])
  if getsettings(username)['Email'] == True:
    context = ssl.create_default_context()
    MAILPASS = os.getenv("MAIL_PASSWORD")
    html = f"""
    <h1>Hello {username}!</h1>
    <p><strong>You have one new notification!</strong></p>
    <p>{notif}</p>
    <p>If you want to disable email notifications, then click <a href="https://OvalEyes.vulcanwm.repl.co/settings">here</a> to to disable them!
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = "OvalEyes New Notification"
    part2 = MIMEText(html, "html")
    message.attach(part2)
    try:
      sendermail = "ovaleyesofficial@gmail.com"
      password = MAILPASS
      gmail_server = smtplib.SMTP('smtp.gmail.com', 587)
      gmail_server.starttls(context=context)
      gmail_server.login(sendermail, password)
      message["From"] = sendermail
      usermail = getuser(username)['Email']
      message["To"] = usermail
      gmail_server.sendmail(sendermail, usermail, message.as_string())
      return True
    except Exception as e:
      print(e)
      return "Verification email not sent, due to some issues."
      gmail_server.quit()
  return True

def clearnotifs(username):
  notifs = getnotifs(username)
  for notif in notifs:
    delete = {"_id": notif['_id']}
    notifscol.delete_one(delete)
  return True

def allseen(username):
  notifs = getnotifs(username)
  myquery = { "Username": username }
  newvalues = { "$set": { "Seen": True } }
  notifscol.update_many(myquery, newvalues)
  return True

def getpost(desc):
  myquery = { "Description": desc }
  mydoc = postscol.find(myquery)
  for x in mydoc:
    return x
  return False

def getpostid(id):
  myquery = { "_id": int(id) }
  mydoc = postscol.find(myquery)
  for x in mydoc:
    return x
  return False

def makepost(username, title, desc, posttype):
  id = random_with_N_digits(10)
  while getuserid(int(id)) == True:
    id = random_with_N_digits(10)
  document = [{
    "_id": id,
    "Author": username,
    "Title": title,
    "Description": desc,
    "Likes": 0,
    "LikesPeople": [],
    "Views": [],
    "Type": posttype,
    "Created": datetime.datetime.now()
  }]
  postscol.insert_many(document)

def viewpost(id, username):
  post = getpostid(str(id))
  if username in post['Views']:
    return True
  else:
    views = post['Views']
    views.append(username)
    del post['Views']
    post['Views'] = views
    delete = {"_id": int(id)}
    postscol.delete_one(delete)
    postscol.insert_many([post])
    return True

def delpost(username, theid):
  post = getpostid(int(theid))
  if post == False:
    return "This is not a real post!"
  if post['Author'] == username:
    delete = {"_id": post["_id"]}
    postscol.delete_one(delete)
    return True
  elif username in mods:
    delete = {"_id": post["_id"]}
    postscol.delete_one(delete)
    addnotif(post['Author'], f"Your post has been deleted!")
    return True
  else:
    return "You cannot delete this post!"

def gettop():
  number = 0
  posts = []
  for post in postscol.find().sort("Likes", -1):
    if number == 10:
      return posts
    posts.append(post)
    number = number + 1

def getnew():
  number = 0
  posts = []
  for post in postscol.find().sort("Created", -1):
    if number == 10:
      return posts
    posts.append(post)
    number = number + 1

def getsettings(username):
  myquery = { "Username": username }
  mydoc = settingscol.find(myquery)
  for x in mydoc:
    return x
  print("not a document")
  return {"Username": username,"Email": False, "Public": False}

def getsettingstof(username):
  myquery = { "Username": username }
  mydoc = settingscol.find(myquery)
  for x in mydoc:
    return True
  return False

def changepublicsettings(username):
  document = getsettings(username)
  if getsettingstof(username) == True:
    delete = {"Username": username}
    settingscol.delete_one(delete)
  old = document['Public']
  if old == False:
    del document['Public']
    document['Public'] = True
    settingscol.insert_many([document])
  if old == True:
    del document['Public']
    document['Public'] = False
    settingscol.insert_many([document])
  return True

def changeemailsettings(username):
  document = getsettings(username)
  if getsettingstof(username) == True:
    delete = {"Username": username}
    settingscol.delete_one(delete)
  old = document['Email']
  if old == False:
    del document['Email']
    document['Email'] = True
    settingscol.insert_many([document])
  if old == True:
    del document['Email']
    document['Email'] = False
    settingscol.insert_many([document])
  return True

def followrequest(follower, following):
  document = [{
    "Follower": follower,
    "Following": following
  }]
  frcol.insert_many(document)

def checkfr(follower, following):
  myquery = { "Follower": follower }
  mydoc = frcol.find(myquery)
  for x in mydoc:
    return x
  return False

def acceptfr(username, follower, following):
  if username != following:
    return "You cannot accept someone else's follow request!"
  theid = checkfr(follower, following)['_id']
  delete = {"_id": theid}
  frcol.delete_one(delete)
  followeruser = getuser(follower)
  followingdoc = followeruser['Following']
  followingdoc.append(following)
  del followeruser['Following']
  followeruser['Following'] = followingdoc
  delete = {"Username": follower}
  profilescol.delete_one(delete)
  profilescol.insert_many([followeruser])
  followinguser = getuser(following)
  followersdoc = followeruser['Followers']
  followersdoc.append(follower)
  del followinguser['Followers']
  followinguser['Followers'] = followersdoc
  delete = {"Username": following}
  profilescol.delete_one(delete)
  profilescol.insert_many([followinguser])
  return True

def allfrs(username):
  myquery = {"Following": username}
  mydoc = frcol.find(myquery)
  allfr = []
  for x in mydoc:
    allfr.append(x)
  return allfr

def declinefr(username, follower, following):
  if username != following:
    return "You cannot decline someone else's follow request!"
  theid = checkfr(follower, following)['_id']
  delete = {"_id": theid}
  frcol.delete_one(delete)
  return True

def alluserposts(username):
  myquery = { "Author":username }
  mydoc = postscol.find(myquery)
  posts = []
  for x in mydoc:
    if x['Type'] == "Public":
      posts.append(x)
  return posts

def editpost(username, theid, desc):
  post = getpostid(int(theid))
  if post == False:
    return "This is not a real post!"
  if post['Author'] == username:
    pass
  elif username in mods:
    pass
  else:
    return "You cannot edit this post!"
  del post['Description']
  post['Description'] = desc
  delete = {"_id": post['_id']}
  postscol.delete_one(delete)
  postscol.insert_many([post])
  return True

def is_human(captcha_response):
  secret = os.getenv("captcha_secret")
  payload = {'response':captcha_response, 'secret':secret}
  response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
  response_text = json.loads(response.text)
  return response_text['success']

def likepost(theid, username):
  post = getpostid(int(theid))
  if username in post['LikesPeople']:
    return "You cannot like a post again!"
  likespeople = post['LikesPeople']
  likespeople.append(username)
  del post['LikesPeople']
  post['LikesPeople'] = likespeople
  likes = post['Likes']
  likes = likes + 1
  del post['Likes']
  post['Likes'] = likes
  delete = {"_id": post['_id']}
  postscol.delete_one(delete)
  postscol.insert_many([post])
  return True

def unlikepost(theid, username):
  post = getpostid(int(theid))
  if username not in post['LikesPeople']:
    return "You cannot unlike a post if you haven't liked it!"
  likespeople = post['LikesPeople']
  likespeople.remove(username)
  del post['LikesPeople']
  post['LikesPeople'] = likespeople
  likes = post['Likes']
  likes = likes - 1
  del post['Likes']
  post['Likes'] = likes
  delete = {"_id": post['_id']}
  postscol.delete_one(delete)
  postscol.insert_many([post])
  return True