from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
request_log = []

@app.route('/log', methods=['GET', 'POST'])
def log_request():
    # Handle file uploads (if any)
    uploaded_files = {}
    if request.files:
        for key, file in request.files.items():
            if file.filename != '':
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                uploaded_files[filename] = {
                    'content_type': file.content_type,
                    'saved_path': filename  # filename only, for url generation
                }

    log_entry = {
        'method': request.method,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'headers': dict(request.headers),
        'args': request.args.to_dict(),
        'body': request.get_json(silent=True) or request.form.to_dict() or request.data.decode(),
        'files': uploaded_files  # Add files info here
    }
    request_log.append(log_entry)
    return "Logged successfully!", 200

@app.route('/requests')
def view_requests():
    return render_template('requests.html', logs=request_log)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Redirect POST to /log with files so they get logged and saved properly
        # But for simplicity, here we just log the files and show success message
        files = request.files.getlist('file')
        if not files or all(f.filename == '' for f in files):
            return "No files selected", 400
        
        # You can forward to /log endpoint or replicate saving here
        uploaded_files = {}
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print("Saving to:", save_path)
                file.save(save_path)
                uploaded_files[filename] = {
                    'content_type': file.content_type,
                    'saved_path': filename
                }

        log_entry = {
            'method': request.method,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'headers': dict(request.headers),
            'args': request.args.to_dict(),
            'body': request.get_json(silent=True) or request.form.to_dict() or request.data.decode(),
            'files': uploaded_files
        }
        request_log.append(log_entry)
        return redirect(url_for('view_requests'))
    else:
        # Show upload form
        return '''
        <h2>Upload File(s)</h2>
        <form method="post" enctype="multipart/form-data">
          <input type="file" name="file" multiple>
          <input type="submit" value="Upload">
        </form>
        <p>Go back to <a href="/requests">Requests Log</a></p>
        '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def home():
    return '''
    <h2>Welcome to the 5G Request Logger!</h2>
    <p>Go to <a href='/requests'>/requests</a> to view logs.</p>
    <p>Go to <a href='/upload'>/upload</a> to upload files.</p>
    '''
@app.route('/files')
def list_uploaded_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_links = [f'<li><a href="/uploads/{f}">{f}</a></li>' for f in files]
    return f"<h2>Uploaded Files</h2><ul>{''.join(file_links)}</ul>"


@app.route('/clear', methods=['POST'])
def clear_logs():
    request_log.clear()
    return '', 204

@app.route('/download')
def download_logs():
    from flask import Response
    import json
    return Response(
        json.dumps(request_log, indent=4),
        mimetype='application/json',
        headers={"Content-Disposition": "attachment;filename=request_logs.json"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
