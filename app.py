import mysql.connector
from flask import Flask, request, jsonify, session, render_template, url_for
import datetime

app = Flask(__name__)
app.secret_key = 'LAXARUN'

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        request.form.email 
    return render_template('login.html')

@app.route('/announcement_board')
def announcement():
    return render_template('announcement.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/faculty')
def faculty():
    return render_template('faculty.html')


def get_faculty_name(email):

    facultydb = mysql.connector.connect(
        host='localhost',
        user='your_db_username',
        password='your_db_password',
        database='your_db_name'
    )

    cursor = facultydb.cursor()

    query = "SELECT name FROM main WHERE email = %s"
    cursor.execute(query, (email,))

    result = cursor.fetchone()

    cursor.close()
    facultydb.close()

    if result:
        return result[0]  
    else:
        return None  

@app.route('/getannouncement')
def get_announcement():
    try:
        # Assuming you have a database connection
        announcementdb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='sf_announcement'
        )
        cursor = announcementdb.cursor()

        # Retrieve announcements from the database
        select_query = "SELECT id, Name, announcement, Date, Time FROM announcements ORDER BY Date DESC, Time DESC"
        cursor.execute(select_query)
        result = cursor.fetchall()

        announcements = []
        for row in result:
            id, name, content, date, time = row
            announcement = {
                'id': id,
                'actor': 'faculty' if name == get_faculty_name(session['email']) else 'student',
                'name': name,
                'content': content,
                'date': date.strftime('%B %d, %Y'),
                'time': time.strftime('%I:%M %p')
            }
            announcements.append(announcement)

        return jsonify(announcements=announcements)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/postannouncement', methods=['POST'])
def post_announcement():
    if 'email' in session and 'actor' in session:
        email = session['email']
        actor = session['actor']
        name = get_faculty_name(email)

        # Get data from the request
        content = request.json.get('content')
        date = request.json.get('date')
        time = request.json.get('time')

        try:
            # Assuming you have a database connection
            announcementdb = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='sf_announcement'
            )
            cursor = announcementdb.cursor()

            # Insert the announcement into the database
            insert_query = "INSERT INTO announcements (Name, announcement, Date, Time) VALUES (%s, %s, %s, %s)"
            values = (name, content, date, time)
            cursor.execute(insert_query, values)
            announcementdb.commit()

            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
        finally:
            cursor.close()
            announcementdb.close()
    else:
        return jsonify({'success': False, 'error': 'Unauthorized access.'})

@app.route('/deleteannouncement', methods=['POST'])
def delete_announcement():
    if 'email' in session and 'actor' in session and session['actor'] == 'faculty':
        email = session['email']
        actor = session['actor']
        name = get_faculty_name(email)

        announcement_id = request.json.get('announcement_id')
        announcement_name = request.json.get('announcement_name')

        if name == announcement_name:
            try:
                # Assuming you have a database connection
                announcementdb = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='',
                    database='sf_announcement'
                )
                cursor = announcementdb.cursor()

                # Delete the announcement from the database
                delete_query = "DELETE FROM announcements WHERE id = %s"
                cursor.execute(delete_query, (announcement_id,))
                announcementdb.commit()

                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
            finally:
                cursor.close()
                announcementdb.close()
        else:
            return jsonify({'success': False, 'error': 'You can only delete your own announcements.'})
    else:
        return jsonify({'success': False, 'error': 'Unauthorized access.'})



if __name__ == '__main__':
    app.run(debug=True)
