import pymongo
import smtplib
import ssl
import random
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
postsdb = client.Posts
postscol = postsdb.Posts
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
    <p><strong>You have signed up for an account in VulcanWM!</strong></p>
    <p>Click <a href='https://VulcanWM.repl.co/verify/{username}/{str(id)}'>here</a> to verify your account</p>
    <p>If you didn't make this account, reply back to this email saying this isn't your account and <strong>DO NOT</strong> click on the link or the user who made the account will get verified with your email!</p>
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = "VulcanWM Verification Email"
    part2 = MIMEText(html, "html")
    message.attach(part2)
    try:
      sendermail = "vulcanwmemail@gmail.com"
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
  notif = {"Username": username, "Notification": notif, "Seen": False}
  notifscol.insert_many([notif])
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

def makepost(username, title, desc):
  id = random_with_N_digits(10)
  while getuserid(int(id)) == True:
    id = random_with_N_digits(10)
  document = [{
    "_id": id,
    "Author": username,
    "Title": title,
    "Description": desc,
    "Likes": 0,
    "Views": [],
    "Created": str(datetime.datetime.now())
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