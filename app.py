import mysql.connector
from flask import Flask, request, jsonify, session, render_template, url_for, redirect, flash, send_from_directory, Response
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)
app.secret_key = 'LAXARUN'
app.config['UPLOAD_FOLDER'] = 'static/resources'

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/faculty')
def faculty():
    return render_template('facultydetails.html')

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
    


@app.route('/resources')
def resources():
    if 'email' not in session or 'actor' not in session:
        return redirect('/')

    db_connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='sf_resources'
    ) 

    cursor = db_connection.cursor()
    select_query = "SELECT * FROM main ORDER BY Date DESC, Time DESC"
    cursor.execute(select_query)
    result = cursor.fetchall()

    cursor.close() 
    db_connection.close()

    resources = []
    for row in result:
        id, name, title, description, Filenames, date, time = row
        resource = {
            'id': id,
            'name': name,
            'title': title,
            'description': description,
            'Filenames': Filenames,
            'date': date,
            'time': time
        }
        resources.append(resource)

    return render_template('resources.html', resources=resources, get_faculty_name=get_faculty_name)

@app.route('/upload_resource', methods=['POST'])
def upload_resource():
    if 'email' not in session or 'actor' not in session:
        return redirect('/')

    if request.method == 'POST':
        try:
            name = get_faculty_name(session['email'])
            title = request.form.get('title')
            description = request.form.get('description')
            files = request.files.getlist('files[]')
            
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(name))
            os.makedirs(folder_path, exist_ok=True)
            
            current_datetime = datetime.now()

            mysql_date_format = current_datetime.strftime('%Y-%m-%d')
            mysql_time_format = current_datetime.strftime('%H:%M:%S')

            db_connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='sf_resources'
            ) 

            filenames_with_paths = []
            for file in files:
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(folder_path, filename)
                    file.save(file_path)
                    filenames_with_paths.append(filename)

            # Convert filenames_with_paths list to a string
            filenames_str = ', '.join(filenames_with_paths)

            cursor = db_connection.cursor()
            insert_query = "INSERT INTO main (Name, Title, Description, Filenames, Date, Time) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (name, title, description, filenames_str, mysql_date_format, mysql_time_format))
            db_connection.commit()
            cursor.close()
            db_connection.close()

            return redirect('/resources')

        except Exception as e:
            print(e)
            return render_template('error.html', error_message=str(e))

    return redirect('/')

# @app.route('/download_resource/<int:resource_id>/<filename>')
# def download_resource(resource_id, filename):
#     db_connection = mysql.connector.connect(
#         host='localhost',
#         user='root',
#         password='',
#         database='sf_resources'
#     ) 

#     cursor = db_connection.cursor()
#     select_query = "SELECT Name, FolderPath FROM resources WHERE id = %s"
#     cursor.execute(select_query, (resource_id,))
#     resource = cursor.fetchone()

#     if resource:
#         name, folder_path = resource
#         folder_path = os.path.join(folder_path, secure_filename(name))
#         file_path = os.path.join(folder_path, secure_filename(filename))

#         cursor.close()
#         db_connection.close()

#         return send_from_directory(folder_path, filename=filename, as_attachment=True)

#     cursor.close()
#     db_connection.close()
#     return render_template('error.html', error_message='Resource not found')

@app.route('/download_resource/<int:resource_id>/<filename>')
def download_resource(resource_id, filename):
    db_connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='sf_resources'
    ) 

    cursor = db_connection.cursor()

    select_query = "SELECT Name, Filenames FROM main WHERE id = %s"
    cursor.execute(select_query, (resource_id,))
    resource = cursor.fetchone()
    print(resource)
    if resource:
        name, filenames_str = resource
        filenames = [filename.strip() for filename in filenames_str.split(',')]
        print(filenames)
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(name))
        print(folder_path)
        if filename in filenames:
            file_path = os.path.join(folder_path, filename)
            cursor.close()
            db_connection.close()
                    # Determine the MIME type based on the file extension
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

            # Create a Flask Response object to send the file with correct MIME type
            response = Response()
            response.headers['Content-Type'] = mime_type
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            response.headers['Content-Length'] = os.path.getsize(file_path)

            response.data = open(file_path, 'rb').read()

            return response

            # return send_from_directory(directory=folder_path, filename=filename, as_attachment=True)
    
    cursor.close()
    db_connection.close()

    return "File not found", 404


@app.route('/delete_resource/<int:resource_id>', methods=['GET', 'POST'])
def delete_resource(resource_id):
    if 'email' not in session or 'actor' not in session:
        return "Unauthorized", 403
    
    db_connection =  mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='sf_resources'
    ) 

    cursor = db_connection.cursor()

    try:
        # Get faculty name and filenames associated with the resource
        select_query = "SELECT Name, Filenames FROM main WHERE id = %s"
        cursor.execute(select_query, (resource_id,))
        resource = cursor.fetchone()

        if resource is None:
            return "Resource not found", 404

        faculty_name = resource[0]
        filenames_str = resource[1]
        filenames = filenames_str.split(', ')  # Split the string into a list of filenames

        # Delete the resource record from the database
        delete_query = "DELETE FROM main WHERE id = %s"
        cursor.execute(delete_query, (resource_id,))
        db_connection.commit()

        # Delete the associated files from the folder
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(faculty_name))
        for filename in filenames:
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)

        return "Success", 200

    except Exception as e:
        print(e)
        return "Error", 500

    finally:
        cursor.close()
        db_connection.close()



@app.route('/discussion')
def discussion():
    return render_template('discussionforum.html')


if __name__ == '__main__':
    app.run(debug=True)
