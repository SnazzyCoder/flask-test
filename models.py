from flask import Flask, session
from flaskext.mysql import MySQL
import resources.config as config
import html
import hashlib
import arrow

app = Flask(__name__, static_url_path="/static")
app.secret_key = config.secret_key

app.config['MYSQL_DATABASE_HOST'] = "remotemysql.com"
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = "ggAVIcwN9H"
app.config['MYSQL_DATABASE_PASSWORD'] = config.db_pass
app.config['MYSQL_DATABASE_DB'] = "ggAVIcwN9H"
mysql = MySQL()
mysql.init_app(app)

# Configuration
salt_string = config.salt_string

def return_single(cmd):
    conn = mysql.connect()
    cursor = conn.cursor()
    
    try: cursor.execute(cmd)
    except Exception as e: print("!!!    error:", e)
    finally: conn.close()
    try:
        return cursor.fetchone()[0]
    except:
        "Nothing"

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
        conn.commit()
    except Exception as e: print("!!!    error:", e)
    finally: conn.close()

    return _res == 1

def follows_user(following, follower=None):
    if not follower: follower = session.get('username')

    return return_single(f'SELECT count(*) from follows where follower="{follower}" and following="{following}"') >= 1

def unfollow(following, follower=None):
    if not follower: follower = session.get('username')

    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        _res = cursor.execute("DELETE FROM follows where follower=%s and following=%s;", (follower, following))
        conn.commit()
    except Exception as e: print("!!!    error:", e)
    finally: 
        cursor.close()
        conn.close()

    return _res == 1

def get_tweets(_for=None):
    if not _for: _for = session.get('username')
    
    conn = mysql.connect()
    cursor = conn.cursor()
    
    # Get tweets
    try:
        cursor.execute("select t.tweet_id, t.username, t.tweet_content, t.tweet_at from tweets as t INNER JOIN (select following from follows where follower=%s limit 600) as f on t.username=f.following order by tweet_at desc limit 600", (_for))
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
        res = cursor.execute('Select username, name, created from users limit 600')
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
        cursor.execute("select tweet_id, tweet_at, tweet_content from tweets where username=%s order by tweet_at desc limit 600", (uname))
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