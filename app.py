import mysql.connector
from flask import Flask, request, jsonify, session, render_template, url_for, redirect, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'LAXARUN'

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/faculty')
def faculty():
    return render_template('faculty.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session and 'actor' in session:
        return redirect('/')
    
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role')

        # Assuming you have a database connection
        logindb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='sf_logininfo'
        )
        cursor = logindb.cursor()

        query = "SELECT email, actor FROM main WHERE email = %s AND password = %s AND actor = %s"
        cursor.execute(query, (email, password, role))
        result = cursor.fetchone()

        cursor.close()
        logindb.close()

        if result:
            session['email'] = email
            session['actor'] = role
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True})
            else:
                return redirect('/')  # Redirect to homepage after successful login
        else:
            error_message = "Invalid credentials or role selection. Please try again."
            flash(error_message, 'error')  # Flash error message

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': error_message})
            else:
                return render_template('login.html')

    return render_template('login.html')


def get_faculty_name(email):

    facultydb = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='sf_facultyinfo'
    )

    cursor = facultydb.cursor()

    query = "SELECT Name FROM main WHERE email = %s"
    cursor.execute(query, (email,))

    result = cursor.fetchone()

    cursor.close()
    facultydb.close()

    if result:
        return result[0]  
    else:
        return None  


@app.route('/create_announcement', methods=['POST'])
def create_announcement():
    if 'email' in session and 'actor' in session and session['actor'] == 'Faculty':
        # Get the content from the form submission
        content = request.form.get('content')
        email = session['email']
        # actor = session['actor']
        name = get_faculty_name(email)
        current_datetime = datetime.now()

        # Format the date and time to match MySQL's DATE and TIME formats
        mysql_date_format = current_datetime.strftime('%Y-%m-%d')
        mysql_time_format = current_datetime.strftime('%H:%M:%S')

        announcementdb = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='sf_announcement'
        )
        cursor = announcementdb.cursor()

        insert_query = "INSERT INTO main (Name, Announcement, Date, Time) VALUES (%s, %s, %s, %s)"
        values = (name, content, mysql_date_format, mysql_time_format)
        cursor.execute(insert_query, values)
        announcementdb.commit()

        cursor.close()
        announcementdb.close()

        return redirect(url_for('announcements'))
    else:
        return redirect('/')
    
@app.route('/announcements', methods=['GET', 'POST'])
def announcements():
    if 'email' not in session or 'actor' not in session:
        return redirect('/')
    
    try:
        announcementdb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='sf_announcement'
        )
        
        cursor = announcementdb.cursor()
        select_query = "SELECT Id, Name, Announcement, Date, Time FROM main ORDER BY Date DESC, Time DESC"
        cursor.execute(select_query)
        result = cursor.fetchall()

        announcements = []
        for row in result:
            id, name, content, date, time = row
            announcement = {
                'id': id,
                'name': name,
                'content': content,
                'date': date,
                'time': time
            }
            announcements.append(announcement)
        
        return render_template('announcement.html', announcements=announcements, get_faculty_name = get_faculty_name)
    except Exception as e:
        # Handle any errors here
        return render_template('error.html', error_message=str(e))
    finally:
        if announcementdb.is_connected():
            cursor.close()
            announcementdb.close()

@app.route('/delete_announcement/<int:announcement_id>', methods=['GET', 'POST'])
def delete_announcement(announcement_id):
    if 'email' in session and 'actor' in session and session['actor'] == 'Faculty':
        try:
            # Connect to the database
            announcementdb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='sf_announcement'
            )
        
            cursor = announcementdb.cursor()

            # Delete the announcement from the database
            delete_query = "DELETE FROM main WHERE Id = %s"
            cursor.execute(delete_query, (announcement_id,))
            announcementdb.commit()

            return "Success", 200
        except Exception as e:
            print(e)
            return "Error", 500  # Return an error response
        finally:
            cursor.close()
            announcementdb.close()
    else:
        return "Unauthorized", 403
    


if __name__ == '__main__':
    app.run(debug=True)
