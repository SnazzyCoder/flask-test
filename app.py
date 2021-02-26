from flask import Flask, redirect, url_for, render_template, request, session, Markup
from flaskext.mysql import MySQL
import html
import hashlib
import resources.config as config
from resources.mailing import send_mail
import arrow

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
global verify
username = ""
verify = True

salt_string = config.salt_string
error_messages = {'db_error': 'Unable to make your entry into our database.'}


def return_single(cmd):
    conn = mysql.connect()
    cursor = conn.cursor()
    
    try: cursor.execute(cmd)
    except Exception as e: print("!!!    error:", e)
    finally: conn.close()
    
    return cursor.fetchone()[0]

def encode_mail(mail):
    return "".join((mail.split('@')[0][:3], '*' * 7, '@',mail.split('@')[1])) 

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

def humanize(time):
    return arrow.get(time).shift(minutes=0).humanize(arrow.utcnow())

def get_name(_username):
    conn = mysql.connect()
    cursor = conn.cursor()
    result = cursor.execute("select name from users where username=%s limit 1;", (_username))
    if int(result) >= 1:
        return cursor.fetchone()[0]
    else:
        return False

def follow_user(following, follower=None):
    if not follower: follower = session.get('username')
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        _res = cursor.execute('INSERT INTO follows (follower, following) values (%s, %s)', (follower, following))
    except Exception as e: print("!!!    error:", e)
    finally: conn.close

    return _res == 1

def follows_user(following, follower=None):
    if not follower: follower = session.get('username')

    return return_single(f'SELECT count(*) from follows where follower="{follower}" and following="{following}"') >= 1

def get_tweets(_for=None):
    if not _for: _for = session.get('username')
    
    conn = mysql.connect()
    cursor = conn.cursor()
    
    # Get tweets
    try:
        cursor.execute("select t.tweet_id, t.username, t.tweet_content, t.tweet_at from tweets as t INNER JOIN (select following from follows where follower=%s limit 600) as f on t.username=f.following order by tweet_at desc limit 100", (_for))
    except Exception as e:
        print("!!!!   error : ", e)
    finally:
        conn.close()
    
    # Decoding
    result = [dict(zip(("tweet_id", "username", "tweet_content", "tweet_at"), tweet)) for tweet in cursor.fetchall()]
    for i in result:
        i['tweet_content'] = html.unescape(i['tweet_content'])
        i['tweet_at'] = humanize(i['tweet_at'])
    return result

def get_email(_username):
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT email from users where username=%s limit 1', (_username))
    except Exception as e: print("!!!    error:", e)
    finally: conn.close()
    
    return cursor.fetchone()[0]


def get_profiles():
    conn = mysql.connect()
    cursor = conn.cursor()
    
    try:
        res = cursor.execute('Select username, name, created from users limit 100')
    except Exception as e:
        print("!!!     error:", e)
    finally:
        conn.close()
    
    result = [dict(zip(("username", "name", "created_at"), tweet)) for tweet in cursor.fetchall()]
    for i in result:
        i['created_at'] = humanize(i['created_at'])
        i['tweets_count'] = get_tweet_count(i['username'])
        i['followers'] = get_follower_count(i['username'])
    
    return result

def update_password(pwd, uname=None):

    pwd = hash_password(pwd)

    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        res = cursor.execute('update users set password=%s where username=%s limit 1;', (pwd, uname))
        conn.commit()
    except Exception as e:
        print("!!!     error:", e)
    finally:
        conn.close()

    return res == 1


def get_his_tweets(uname):
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        cursor.execute("select tweet_id, tweet_at, tweet_content from tweets where username=%s order by tweet_at desc limit 100", (uname))
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
    result = [list(i) for i in result]
    result = [i.append(get_name(i[0])) or i for i in result]
    result
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

def explore_users(data):
    pass

def get_created_at(uname=None):
    if not uname: uname = session.get('username')
    return return_single(f"select created from users where username='{uname}'")

def get_user_details(uname):
    details = {
        'username': uname,
        'name': get_name(uname),
        'number_tweets': get_tweet_count(uname),
        'followers': get_follower_count(uname),
        'created_at': humanize(get_created_at(uname)),
        'tweets': get_his_tweets(uname)
    }
    
    return details

def check_login(_username, password):
    conn = mysql.connect()
    cursor = conn.cursor()

    try: result = cursor.execute(f"SELECT * FROM users WHERE username=%s AND password=%s LIMIT 1;", (_username, password))
    except Exception as e: return e
    finally: conn.close()
    
    return result >= 1

def valid_username(_username):
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
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        app.jinja_env.globals.update(username=session.get('username'))
        success = tweet(request.form['tweet'])
        return render_template('home.html', tweet_sucess=success, tweets=get_tweets())
    
    app.jinja_env.globals.update(username=session.get('username'))
    return render_template('home.html', tweets=get_tweets())

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        username = request.form.get('username').lower()
        result = check_login(username, hash_password(request.form.get('password')))
        if result == True:
            session['username'] = username
            app.jinja_env.globals.update(username=username)
            return redirect(url_for('home'))
        elif type(result) == str:
            return render_template("login.html", error=type(result).__name__) 
        else:
            return render_template("login.html", failed = True)
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for('login'))

@app.route("/signup", methods=["POST", "GET"])
def signup(error=None):
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == "POST":
        conn = mysql.connect()
        cursor = conn.cursor()
        
        username, name = request.form['username'].lower(), request.form['name'].title()
        if not valid_username(username):
            return render_template("signup.html", error=Markup("Username already exists, login <a href='/login'>here</a>. EXISTING_USERNAME_ERROR"))
        try: 
            result = cursor.execute("INSERT INTO users (username, name, password, email) values (%s, %s, %s, %s)", (username, name, hash_password(request.form['password']), request.form['email']))
            conn.commit()
        except Exception as e:
            return redirect(url_for('signup', error=e))
        finally: conn.close()
        
        if result >= 1:
            session['username'] = username
            app.jinja_env.globals.update(username=username)
            return render_template("home.html")
        return render_template("signup.html", error=error_messages['db_error'])
        
    return render_template("signup.html", error=error)

@app.route('/forgot', methods=['POST', "GET"])
def forgot():
    if request.method == 'POST':
        # Check if Step1
        onstep1 = False
        try: 
            global tusername
            tusername = request.form.get('username').lower()
            onstep1 = True
        except:
            try:
                get_code = request.form.get('code')
                onstep2 = True
            except:
                print("!!!    error: Double Exception error!")
                return render_template('forgot.html', error='Double exception error')
                
        if onstep1:
            if valid_username(tusername):
                return render_template('forgot.html', error="The username does not exist. Please check.")
            global email
            email = get_email(tusername)
            global code
            code = send_mail(email)
            return render_template('forgot.html', step2=True, to=encode_mail(email))
            
        elif onstep2 and code:
            if int(get_code) == code:
                session['username'] = tusername
                global verify
                verify = False
                return redirect(url_for('change_password'))
            else:
                return render_template('forgot.html', step2=True, to=encode_mail(email), error="The code you entered was invalid. Retry")
        return render_template('forgot.html', error="The function did not return a valid html page, i.e. no view function was executed", step1=True)
        
    # Basic checking
    if 'username' in session:
        return redirect(url_for('home'))
    
    # Code here
    return render_template('forgot.html', step1=True)
    

@app.route('/user/<uname>', methods=['POST', 'GET'])
def profile(uname=None):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        follow_user(uname)
        _res = get_user_details(uname)
        return render_template('profile.html', data=_res, following=follows_user(uname))

    if not uname: uname = session.get('username')
    
    _res = get_user_details(uname)
    return render_template('profile.html', data=_res, following=follows_user(uname))

@app.route('/user')
def my_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    uname = session.get('username')
    _res = get_user_details(uname)
    return render_template('profile.html', data=_res, following=None)

@app.route("/user/followers")
@app.route('/user/<uname>/followers')
def get_profile_followers(uname=None):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if not uname: uname = session.get('username')

    _res = [dict(zip(('username', 'followers', 'follower_count', )))]
    return render_template('followers.html', data=_res)

@app.route("/explore")
def explore():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('explore.html', data=get_profiles())

@app.route("/change_password", methods=["POST", "GET"])
def change_password():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        if not verify:
            _pass = request.get('password')
            chpwd = update_password(_pass, session.get('username'))
            if chpwd: 
                global verify
                verify = True
                return render_template('change_password.html', success=True)
            else:
                return render_template('change_password.html', error="Password was not updated. Retry in a moment")
        else:
            _pass = request.get('password')
            if check_login(session.get('username'), _pass):
                verify = False
                return render_template('change_password.html')
            else:
                return render_template('change_password.html', step1=True, error='The password was wrong. Please retry.')

    if not verify:
        app.jinja_env.globals.update(username=session.get('username'))
        return render_template('change_password.html')

    return render_template('change_password.html', step1=True)
    

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # DEBUG is SET to TRUE. CHANGE FOR PRODUCTION
    app.run(port=5000)
    # pass
