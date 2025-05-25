from flask import Flask, render_template, session, redirect, url_for, request, flash
import sqlite3 as sql
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = '5a75e4536df26160a719ab6260a5c4f5'

def create_tables():
    with sql.connect('users.db') as con:
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nm TEXT NOT NULL UNIQUE,
                pwd TEXT NOT NULL
                                            )
                    ''')
        con.commit()




def create_journals():
    with sql.connect('journals.db') as con:
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                heading TEXT,
                entry TEXT NOT NULL,
                user_id TEXT NOT NULL
                                            )
                    ''')
        con.commit()


def check_user(name, password):
    with sql.connect('users.db') as con:
        cur = con.cursor()
        cur.execute("SELECT pwd FROM users where nm = ?" , (name,))
        data = cur.fetchone()
        if data and check_password_hash(data[0], password):
            return True
        return False


def check_ext_user(nm):
    with sql.connect('users.db') as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM users where nm = ?", (nm,))
        data = cur.fetchone()
        if data:
            return True
        return False



@app.route('/')
def index():
    if 'username' in session :
        username = session['username']
        with sql.connect('journals.db') as con:
                cur = con.cursor()
                cur.execute('SELECT * FROM journals WHERE user_id = ? ORDER BY date DESC', (username,))
                entries = cur.fetchall()
        return render_template('home.html', username = username,journals = entries)
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')
    

@app.route('/existing_user', methods = ['POST', 'GET'])
def existing_user():
    if request.method == 'POST':
        nm = request.form['nm']
        pwd = request.form['pwd']
        if check_user(nm, pwd):
            session['username'] = nm
            flash('login successfull')
            return redirect(url_for('index'))
        else:
            return "Login failed. <a href='login'>Try again</a> or <a href='index'>return Home </a> or <a href='signup'> Sign Up </a>"



@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/new_user', methods = ['POST', 'GET'])
def new_user():
    if request.method == 'POST':
        nm = request.form['nm']
        pwd = request.form['pwd']
        hashed_pwd = generate_password_hash(pwd)
        if not check_ext_user(nm):
            try:
                session['username'] = nm
                with sql.connect('users.db') as con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO users (nm, pwd) VALUES(?,?)",(nm,hashed_pwd))
                    con.commit()
                    flash('Sign up successfull')
        
            except:
                con.rollback()
                flash('error in signing up')
        
            finally: 
                return redirect(url_for('index'))


        else:
            flash("Signing up failed.,User exist. Try different user name or Try logging in")
            return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('logout sucessfull')
    return redirect(url_for('index'))


@app.route('/new_journal')
def new_journal():
    return render_template('/journal.html')


@app.route('/journal', methods = ['POST', 'GET'])
def journal():
    if request.method == 'POST':
        date = request.form['date']
        heading = request.form['heading']
        entry = request.form['entry']
        user_id = session['username']

        try:
            with sql.connect('journals.db') as con:
                cur = con.cursor()
                cur.execute("INSERT INTO journals (date,heading,entry,user_id) VALUES(?,?,?,?)", (date,heading,entry,user_id))
                con.commit()
                flash("Journal added ! \n :)")
                return redirect(url_for('index'))
        except:
            con.rollback()
            flash('Failed to add Journal')
            return redirect(url_for('new_journal'))
        
    else:
        return redirect(url_for('new_journal'))

@app.route('/journals/<int:journal_id>')
def view_journal(journal_id):
    with sql.connect('journals.db') as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('SELECT * FROM journals WHERE id = ? AND user_id = ?', (journal_id, session['username']))
        check = cur.fetchone()
        if check is None:
            flash("You don't have permission to access this journal")
            return redirect(url_for('index'))
        cur.execute('SELECT * FROM journals WHERE id=?',(journal_id,))
    return render_template('view_journal.html', entry=check)


@app.route('/journals/delete/<int:journal_id>')
def delete_journal(journal_id):
    try:
        with sql.connect('journals.db') as con:
            cur = con.cursor()
            cur = con.cursor()
            cur.execute('SELECT * FROM journals WHERE id = ? AND user_id = ?', (journal_id, session['username']))
            check = cur.fetchone()
            if check is None:
                flash("You don't have permission to access this journal")
                return redirect(url_for('index'))
            cur.execute('DELETE FROM journals WHERE id = ?',(journal_id,))
            con.commit()
            flash('Successfully deleted')
    except:
        flash('Unable to delete')
    finally:
        return redirect(url_for('index'))

@app.route('/journals/edit/<int:journal_id>', methods=['GET', 'POST'])
def edit_journal(journal_id):
    if request.method == 'GET':
        try:
            with sql.connect('journals.db') as con:
                con.row_factory = sql.Row
                cur = con.cursor()
                cur.execute('SELECT * FROM journals WHERE id = ? AND user_id = ?', (journal_id, session['username']))
                check = cur.fetchone()
                if check is None:
                    flash("You don't have permission to access this journal")
                    return redirect(url_for('index'))
                return render_template('edit_journal.html', entry = check)
        except:
            flash('Unable to edit Journal')
            return redirect(url_for('index'))
    else:
        heading = request.form['heading']
        entry = request.form['entry']
        try:
            with sql.connect('journals.db') as con:
                con.row_factory = sql.Row
                cur = con.cursor()
                cur.execute('SELECT * FROM journals WHERE id = ? AND user_id = ?', (journal_id, session['username']))
                check = cur.fetchone()
                if check is None:
                    flash("You don't have permission to access this journal")
                    return redirect(url_for('index'))
                cur.execute('UPDATE journals SET heading = ?, entry = ? WHERE id = ?', (heading,entry,journal_id))
                con.commit()
                return redirect(url_for('view_journal', journal_id=journal_id))
        except:
            flash('Unable to edit Journal')
            return redirect(url_for('index'))        

 



create_journals()
create_tables()
if __name__ == '__main__':
    app.run(debug = True)


