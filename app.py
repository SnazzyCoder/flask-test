from flask import Flask,redirect,url_for,render_template,request
from flaskext.mysql import MySQL


app=Flask(__name__)

app.config['MYSQL_DATABASE_HOST'] = "remotemysql.com"
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = "ggAVIcwN9H"
app.config['MYSQL_DATABASE_PASSWORD'] = "dEl1QjNO73"
app.config['MYSQL_DATABASE_DB'] = "ggAVIcwN9H"
mysql = MySQL()
mysql.init_app(app)


@app.route('/',methods=['GET','POST'])
def home():
    if request.method=='POST':
        # Handle POST Request here
        conn = mysql.connect()
        cursor = conn.cursor()
        
        try: 
            cursor.execute(f"INSERT INTO tweets (user_id, tweet_content) values ('{random.randint(100000000, 999999999)}', '{request.form['tweet']}')")
            success = True
        except Exception as e:
            print("!!!!   error : ", e)
        finally: 
            conn.close()
        
        try: success
        except: success = False
        
        return render_template('home.html', tweet_sucess=success)
    return render_template('home.html')

if __name__ == '__main__':
    #DEBUG is SET to TRUE. CHANGE FOR PRODUCTION
    app.run(port=5000, debug=True)
