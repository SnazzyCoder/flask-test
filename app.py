from flask import Flask, redirect, url_for, render_template, request, session
from flaskext.mysql import MySQL
import random
import html
import hashlib
import resources.config as config
import os, arrow

app = Flask(__name__)
app.secret_key = config.secret_key

app.config['MYSQL_DATABASE_HOST'] = "remotemysql.com"
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = "ggAVIcwN9H"
app.config['MYSQL_DATABASE_PASSWORD'] = config.db_pass
app.config['MYSQL_DATABASE_DB'] = "ggAVIcwN9H"
mysql = MySQL()
mysql.init_app(app)

global username
username = ""

salt_string = config.salt_string
error_messages = {'db_error': 'Unable to make your entry into our database.'}

def tweet(content: str, by=None):
    content = html.escape(content)
    if not by:
        by = session.get('username')
    # Handle POST Request here
    conn = mysql.connect()
    cursor = conn.cursor()
    
    try: 
        cursor.execute(f"INSERT INTO tweets (username, tweet_content) values (%s, %s)", (by, content))
        conn.commit()
        success = True
    except Exception as e:
        print("!!!!   error : ", e)
    finally: 
        conn.close()
    
    try: success
    except: success = False
    
    return success

def get_name(_username):
    conn = mysql.connect()
    cursor = conn.cursor()
    result = cursor.execute("select name from users where username=%s limit 1;", (_username))
    if int(result) >= 1:
        return cursor.fetchone()[0]
    else:
        return False

def get_tweets(_for=None):
    if not _for: _for = session.get('username')
    
    conn = mysql.connect()
    cursor = conn.cursor()
    
    #get following
    try:
        cursor.execute("select following from follows where follower=%s limit 600", (_for))
    except Exception as e:
        print("!!!!   error : ", e)

    # Make tuple out of following
    _raw_res = [str(i[0]) for i in cursor.fetchall()]
    _res = ", ".join(_raw_res)
    
    # Get tweets
    try:
        cursor.execute("select * from tweets where username in (%s) order by tweet_at desc limit 20", (_res))
    except Exception as e:
        print("!!!!   error : ", e)
    finally:
        conn.close()
    
    # Decoding
    result = [dict(zip(("tweet_id", "username", "tweet_content", "tweet_at"), tweet)) for tweet in cursor.fetchall()]
    for i in result:
        i['tweet_content'] = html.unescape(i['tweet_content'])
        i['tweet_at'] = arrow.get(i['tweet_at']).shift(minutes=0).humanize(arrow.utcnow())
    return result

def get_his_tweets(uname):
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        cursor.execute("select tweet_id, tweet_at, tweet_content from tweets where username=%s order by tweet_at desc limit 20", (uname))
    except Exception as e:
        print("!!!!   error : ", e)
    finally:
        conn.close()

    # Decoding
    result = [dict(zip(("tweet_id", "tweet_at", "tweet_content"), tweet)) for tweet in cursor.fetchall()]
    for i in result:
        i['tweet_content'] = html.unescape(i['tweet_content'])
        i['username'] = uname
        i['tweet_at'] = arrow.get(i['tweet_at']).shift(minutes=0).humanize(arrow.utcnow())
    return result
    
def get_follower_count(uname=None):
    if not uname: uname = session.get('username')
    
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute("Select count(follow_id) from follows where following=%s", (uname))
    except Exception as e: print("!!!!    error :", e) 
    finally: conn.close()
    
    return cursor.fetchone()[0]

def get_his_followers(uname):
    if not uname: uname = session.get('username')
    
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute("Select follower from follows where following=%s", (uname))
    except Exception as e: 
        print("!!!!    error :", e)
        return
    finally: conn.close()
    
    # Decoding
    result = cursor.fetchall()
    for i in result:
        i = list(i)
        name = get_name(uname)
        i.append(name)
    result = [dict(zip(("username", "name"), follower)) for follower in result]
    return result

def get_tweet_count(uname):
    conn = mysql.connect()
    cursor = conn.cursor()
    
    try: res = cursor.execute("SELECT count('tweet_id') from tweets where username=%s", (uname))
    except Exception as e:
        print("!!!!   error : ", e)
    finally:
        conn.close()
    
    _res = cursor.fetchone()[0]
    try: return int(_res)
    except: return _res
    
def get_user_details(uname):
    details = {
        'number_tweets': get_tweet_count(uname),
        'followers': get_follower_count(uname),
        'tweets': get_tweets(uname)
    }
    
    return details

def check_login(_username, password):
    conn = mysql.connect()
    cursor = conn.cursor()

    try: result = cursor.execute(f"SELECT * FROM users WHERE username=%s AND password=%s LIMIT 1;", (_username, password))
    except Exception as e: return e
    finally: conn.close()
    
    return result >= 1

def check_username(_username):
    conn = mysql.connect()
    cursor = conn.cursor()

    try: result = cursor.execute(f"SELECT * FROM users WHERE username=%s LIMIT 1;", (_username))
    except Exception as e: return e
    finally: conn.close()
    
    return result == 0

def hash_password(raw: str):
    # Salting the raw password
    temp = ''
    for pos, char in enumerate(raw):
        temp += char
        if pos % 3 == 0:
            temp += salt_string
            
    return hashlib.sha224(temp.encode('utf-8')).hexdigest()

@app.route('/',methods=['GET','POST'])
def home():
    
    if request.method=='POST':
        success = tweet(request.form['tweet'])
        return render_template('home.html', username=session.get("username"), tweet_sucess=success, tweets=get_tweets())
    
    if 'username' in session:
        return render_template('home.html', tweets=get_tweets(), username=session.get('username'))
    return redirect(url_for('login'))

@app.route("/login", methods=["POST", "GET"])
def login(recent=False):
    if request.method == 'POST':
        username = request.form.get('username').lower()
        result = check_login(username, hash_password(request.form.get('password')))
        if result == True:
            session['username'] = username
            return redirect(url_for('home'))
        elif type(result) == str:
            return render_template("login.html", error=type(result).__name__) 
        else:
            return render_template("login.html", failed = True)
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template("login.html", recent=recent)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for('login', recent=True))

@app.route("/signup", methods=["POST", "GET"])
def signup(error=None):
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == "POST":
        conn = mysql.connect()
        cursor = conn.cursor()
        
        username, name = request.form['username'].lower(), request.form['name'].title()
        if not check_username(username):
            return render_template("signup.html", error="Username already exists, please try another username.")
        try: 
            result = cursor.execute("INSERT INTO users (username, name, password, email) values (%s, %s, %s, %s)", (username, name, hash_password(request.form['password']), request.form['email']))
            conn.commit()
        except Exception as e:
            return redirect(url_for('signup', error=e))
        finally: conn.close()
        
        if result >= 1:
            session['username'] = username
            return render_template("home.html")
        return render_template("signup.html", error=error_messages['db_error'])
        
    return render_template("signup.html", error=error)

@app.route('/user')
@app.route('/user/<uname>')
def get_profile(uname=None):
    if not uname: uname = session.get('username')
    
    _res = get_user_details(uname)
    return render_template('profile.html', data=_res, username=uname)

@app.route("/user/followers")
@app.route('/user/<uname>/followers')
def get_profile_followers(uname):
    _res = get_user_details(uname)
    return render_template('profile.html', data=_res, username=uname)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # DEBUG is SET to TRUE. CHANGE FOR PRODUCTION
    app.run(port=5000, debug=True)
    # pass
