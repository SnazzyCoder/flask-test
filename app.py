from flask import redirect, url_for, render_template, request, session, Markup
import resources.config as config
from resources.mailing import send_mail
from models import *

global username
global verify
username = ""
verify = True

# Configuration
error_messages = {'db_error': 'Unable to make your entry into our database.'}

# App Starts
@app.route('/',methods=['GET','POST'])
def home():
    alll = request.args.get('all') == 'true'

    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        app.jinja_env.globals.update(username=session.get('username'))
        success = tweet(request.form['tweet'])
        return render_template('home.html', tweet_sucess=success, tweets=get_tweets(followers_only=False if alll else True), all=alll)
    
    app.jinja_env.globals.update(username=session.get('username'))
    return render_template('home.html', tweets=get_tweets(followers_only=False if alll else True), all=alll)


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
    
    # Handles Follow
    if request.method == 'POST':
        follow_user(uname)
        _res = get_user_details(uname)
        return render_template('profile.html', data=_res, following=follows_user(uname))

    # Returns self id if not defined
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

@app.route("/unfollow/<uname>", methods=["GET", "POST"])
def dontfollow(uname):
    res = unfollow(uname)
    return redirect(url_for("profile", uname=uname))

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
    try:
        verify
        if not verify:
            app.jinja_env.globals.update(username=session.get('username'))
            return render_template('change_password.html')
    except: print("Verify is not declared")

    return render_template('change_password.html', step1=True)
    
@app.route("/version")
def version():
    return render_template("version.html", version=config.version)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # DEBUG is SET to TRUE. CHANGE FOR PRODUCTION
    app.run(port=5000, debug=True)
    # pass
