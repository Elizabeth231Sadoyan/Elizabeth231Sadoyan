from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from configparser import ConfigParser
import mysql.connector.pooling
import hashlib

app = Flask(__name__)
auth = HTTPBasicAuth()


config = ConfigParser()
config.read("config.yml")


mydb = config["database"]


connectionpool = (mysql.connector.pooling.MySQLConnectionPool(pool_name="example_pool",
                                                             pool_size=20,
                                                             autocommit=True,
                                                             **mydb))


@auth.verify_password
def user_login(username, password):
    connect = connectionpool.get_connection()
    cursor = connect.cursor()

    hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()

    cursor.execute("SELECT username, password FROM users WHERE username=" + '"' + username + '"'
                   + "AND password=" + '"' + hashed + '"')
    result_users = cursor.fetchall()
    users = dict((x, y) for x, y in result_users)
    for username, password in users.items():
        if username in users.keys() and password in users.values():
            return username


@app.route('/', methods=['GET'])
@auth.login_required
def home():
    return "Hello, {}".format(auth.current_user())


@app.route('/users/details', methods=['POST'])
@auth.login_required
def user_details():

    connect = connectionpool.get_connection()
    cursor = connect.cursor()

    data_request = request.get_json()

    current_pwd = hashlib.sha256(data_request["current_pwd"].encode('utf-8')).hexdigest()
    new_pwd = hashlib.sha256(data_request["new_pwd"].encode('utf-8')).hexdigest()
    confirm_pwd = hashlib.sha256(data_request["confirm_pwd"].encode('utf-8')).hexdigest()
    chat = data_request["tg_chat"]
    id = data_request["tg_id"]

    cursor.execute("SELECT password FROM users WHERE username=" + '"' + auth.current_user() + '"')
    result_users = cursor.fetchall()[0][0]
    if current_pwd == result_users:
        if new_pwd == confirm_pwd:
            cursor.execute("UPDATE users SET password=%s, tg_chat=%s, tg_id=%s WHERE username=%s",
                           (new_pwd, chat, id, auth.current_user()))

            return 'Success'


@app.route('/users/sites', methods=['POST'])
@auth.login_required
def site_db():

    connect = connectionpool.get_connection()
    cursor = connect.cursor()

    data_request = request.get_json()
    site_name = data_request["site_name"]
    url = data_request["url"]

    cursor.execute("SELECT owner, url FROM sites_list WHERE owner=" + '"' + auth.current_user() + '"')
    result = dict((x, y) for x, y in cursor.fetchall())

    if auth.current_user() not in result.keys():
        sql = "INSERT INTO sites_list (owner, site_name, url) VALUES(%s, %s, %s)"
        val = (auth.current_user(), site_name, url)
        cursor.execute(sql, val)
        return "Success"

    elif url not in result.values():
        sql1 = "INSERT INTO sites_list (owner, site_name, url) VALUES(%s, %s, %s)"
        val1 = (auth.current_user(), site_name, url)
        cursor.execute(sql1, val1)
        return "Success"

    else:
        return "Already in the list"


@app.route('/users/keywords', methods=['POST'])
@auth.login_required
def keyword_db():
    connect = connectionpool.get_connection()
    cursor = connect.cursor()

    data_request = request.get_json()
    keywords = data_request["keywords"]

    cursor.execute("SELECT owner, keywords FROM keywords WHERE owner=" + '"' + auth.current_user() + '"')
    result = dict((x, y) for x, y in cursor.fetchall())

    if auth.current_user() not in result.keys():
        sql = "INSERT INTO keywords (owner, keywords) VALUES(%s, %s)"
        val = (auth.current_user(), keywords)
        cursor.execute(sql, val)
        return "Success"

    elif keywords not in result.values():
        sql1 = "INSERT INTO keywords (owner, keywords) VALUES(%s, %s)"
        val1 = (auth.current_user(), keywords)
        cursor.execute(sql1, val1)
        return "Success"

    else:
        return "Already in the list"


@app.route('/users/admins', methods=['POST'])
@auth.login_required
def admins_desk():

    connect = connectionpool.get_connection()
    cursor = connect.cursor()
    data_request = request.get_json()

    cursor.execute("SELECT username, role FROM users WHERE username=" + '"' + auth.current_user() + '"')
    result = dict((x, y) for x, y in cursor.fetchall())
    for v in result.values():
        if v == 'admin':
            first_name = data_request["first_name"]
            last_name = data_request["last_name"]
            name = data_request["username"]
            email = data_request["email"]
            tg_chat = data_request["tg_chat"]
            tg_id = data_request["tg_id"]
            role = data_request['role']

            hashed_password = hashlib.sha256(data_request["password"].encode('utf-8')).hexdigest()
            cursor.execute("SELECT username FROM users WHERE username = " + '"' + name + '"')
            result1 = cursor.fetchall()

            if len(result1) == 0:
                while True:
                    sql = ("INSERT INTO users (first_name, last_name, email, username, password, tg_chat, tg_id, role)"
                           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
                    val = (first_name, last_name, email, name, hashed_password, tg_chat, tg_id, role)
                    cursor.execute(sql, val)
                    return 'Success'
            else:
                return "Account already exists!"
        else:
            return "Access Denied! You must be an admin to open this page!"


if __name__ == '__main__':
    app.run()
