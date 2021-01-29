from flask import Flask, redirect, url_for, render_template, request, session
from flaskext.mysql import MySQL
import random
import html
import hashlib
import resources.config as config

app = Flask(__name__)

app.config['MYSQL_DATABASE_HOST'] = "remotemysql.com"
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = "ggAVIcwN9H"
app.config['MYSQL_DATABASE_PASSWORD'] = config.db_pass
app.config['MYSQL_DATABASE_DB'] = "ggAVIcwN9H"
mysql = MySQL()
mysql.init_app(app)


conn = mysql.connect()
cursor = conn.cursor()

