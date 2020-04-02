#!/usr/bin/env python

from flask import Flask, request, abort, jsonify, Response, render_template, url_for, redirect, flash
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user, logout_user
from flaskext.markdown import Markdown
from validate_email import validate_email

import re
import sqlite3
import string
import json
import bcrypt
import secrets
import config

app = Flask(__name__)
login_manager=LoginManager(app)
login_manager.session_protection=None
Markdown(app)
app.config['SECRET_KEY']=config.secret_key
USER_DB_PATH=config.USER_DB_PATH
DB_PATH=config.DB_PATH

def get_users():
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT username from credentials")
    results=cursor.fetchall()
    conn.close()
    if len(results)==1:
        return i[0]
    else:
        return [i[0] for i in results]

#User class for managing login
class User(UserMixin):
    user_database=get_users()
    def __init__(self,username):
        self.id=username
    @classmethod
    def get(cls,id):
        return cls.user_database.get(id)


@login_manager.user_loader
def load_user(userid):
    if userid in get_users():
        return User(userid)
    else:
        return None

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged out','success')
    return redirect('/')

def get_unapproved_list():
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM groups where approved!='True'")
    results=cursor.fetchall()
    conn.close()
    return [{'id':i[0],'name':i[1],'description':i[2],'lat':i[3],'lng':i[4],'contact':i[5],'desc_location':i[6]} for i in results]

def get_approved_list():
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT id,name,description,lat,lng,contact,desc_location FROM groups where approved='True'")
    results=cursor.fetchall()
    conn.close()
    return [{'id':i[0],'name':i[1],'description':i[2],'lat':i[3],'lng':i[4],'contact':i[5],'desc_location':i[6]} for i in results]


def approve(group_id):
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute("UPDATE groups SET approved='True' where id=?",(group_id,))
    conn.commit()
    conn.close()
    return group_id

def submit_data(i):
    conn=sqlite3.connect(DB_PATH)
    cursor=conn.cursor()
    cursor.execute("INSERT into groups (name,description,lat,lng,approved,desc_location,contact) VALUES (?,?,?,?,?,?,?)",(i['group_name'],i['group_description'],i['lat'],i['lng'],'False',i['group_location'],i['contact']))
    conn.commit()
    conn.close()


@app.route("/",methods=['GET','POST'])
@app.route("/map",methods=['GET','POST'])
def show_map():
    if request.method=='POST':
        submit_data(request.form)
        flash("Successfully submitted group! Thank you!","success")

    approved_list=get_approved_list()
    return render_template("map.html",data=approved_list)

@app.route("/add-group")
def add_group():
    approved_list=get_approved_list()
    return render_template("add-group.html",data=approved_list)


#@app.route('/list-groups')
def list_groups():
            approved_list=get_approved_list()
            return jsonify(approved_list)

@app.route('/moderate',methods=['GET','POST'])
@login_required
def mod_page():
        if request.method=='POST':
            for i in request.form.getlist('to_approve'):
                approve(i)
                flash('Approved '+i,"success")
        unapproved_list=get_unapproved_list()
        return render_template("moderate.html",unapproved_list=unapproved_list)

@app.route('/view',methods=['GET','POST'])
@login_required
def view_unapproved():
        if request.method=='GET':
            unapproved_list=get_unapproved_list()
            return jsonify(unapproved_list)

        if request.method=='POST':
            for i in request.form.getlist('to_approve'):
                approve_resource(i)
                flash('Approved '+i,"success")

def validate_credentials(username,password):
    #Connect to database, check is password is correct for particular user
    conn=sqlite3.connect(USER_DB_PATH)
    cursor=conn.cursor()
    cursor.execute("SELECT hashed_pw,active from credentials WHERE username=?",(username,))
    results=cursor.fetchall()
    conn.close()
    if not results:
        return False

    hashed=results[0][0]
    if bcrypt.checkpw(password.encode(),hashed) and results[0][1]=='True':
        return True
    else:
        return False

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_credentials(username,password):
            id = username
            user = User(id)
            login_user(user)
            flash('Logged in successfully','success')
            return redirect(request.args.get('next') or "/")
        else:
            flash('Logged in successfully','danger')
    return render_template('login.html')

if __name__=='__main__':
    app.run(debug=True, host="localhost", port=5000)
