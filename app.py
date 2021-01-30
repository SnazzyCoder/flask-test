from flask import Flask, redirect, url_for, render_template, request, session
from flaskext.mysql import MySQL
import random
import html
import hashlib
import resources.config as config
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['MYSQL_DATABASE_HOST'] = "remotemysql.com"
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = "ggAVIcwN9H"
app.config['MYSQL_DATABASE_PASSWORD'] = config.db_pass
app.config['MYSQL_DATABASE_DB'] = "ggAVIcwN9H"
mysql = MySQL()
mysql.init_app(app)

global username
salt_string = 'A6gX5'
error_messages = {'db_error': 'Unable to make your entry into our database.'}

def tweet(content: str):
    content = html.escape(content)
    
    # Handle POST Request here
    conn = mysql.connect()
    cursor = conn.cursor()
    
    try: 
        cursor.execute(f"INSERT INTO tweets (username, tweet_content) values ('%s', %s)", (session['username'], content))
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

def get_tweets():
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute("select * from tweets limit 10")
    except Exception as e:
        print("!!!!   error : ", e)
    finally:
        conn.close()
    
    # Decoding
    result = [dict(zip(("tweet_id", "username", "tweet_content", "tweet_at"), tweet)) for tweet in cursor.fetchall()]
    for i in result:
        i['tweet_content'] = html.unescape(i['tweet_content'])
        i['name'] = get_name(i['username'])
    return result


def check_login(_username, password):
    conn = mysql.connect()
    cursor = conn.cursor()
    
    try: result = cursor.execute(f"SELECT * FROM users WHERE username=%s AND password=%s LIMIT 1;", (_username, password))
    except Exception as e: return e
    finally: conn.close()
    
    return result >= 1
    
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
        return render_template('home.html', tweet_sucess=success, tweets=get_tweets())
    
    if 'username' in session:
        return render_template('home.html', tweets=get_tweets())
    return redirect(url_for('login'))

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
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
        
        username, name = request.form['username'], request.form['name']
        try: 
            result = cursor.execute("INSERT INTO users (username, name, password) values (%s, %s, %s)", (username, name, hash_password(request.form['password'])))
            conn.commit()
        except Exception as e:
            return redirect(url_for('signup', error=e))
        finally: conn.close()
        if result >= 1:
            session['username'] = request.form['username']
            return render_template("home.html")
        return redirect(url_for('signup', error=error_messages['db_error']))
        
    return render_template("signup.html", error=error)

if __name__ == '__main__':
    # DEBUG is SET to TRUE. CHANGE FOR PRODUCTION
    app.run(port=5000, debug=True)
    # pass
