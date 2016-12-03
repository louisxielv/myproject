import os

from flask import Flask, request, redirect, url_for, flash, send_from_directory, render_template
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import FileField, SubmitField

UPLOAD_FOLDER = '/Users/chet/Google Drive/NYU/16fall/db/project'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

import base64
import json
from urllib import parse, request


class Imgur(object):
    """
    Simple class for handling Imgur image upload, and deletion
    """

    API_URL = "https://api.imgur.com/3/image"

    def __init__(self):  # app=None, client_id=None, **kwargs):
        # if not client_id: # and not app.config.get("IMGUR_ID", None):
        #     raise Exception("Missing client id")
        self.client_id = '5b2af5db85fc9a1'  # or app.config.get("IMGUR_ID")
        # if 'api' in kwargs:
        #     self.API_URL = kwargs["api"]

    def _get_api(self):
        return self.API_URL

    def _add_authorization_header(self, additional=dict()):
        """
        Builds authorization headers for anonymous users
        """

        headers = dict(
            Authorization="Client-ID " + self.client_id
        )
        headers.update(additional)
        return headers

    def _build_send_request(self, image=None, params=dict()):
        """
        Build request for sending an image
        """

        if not image:
            raise Exception("Missing image object")

        b64 = base64.b64encode(image.read())

        data = dict(
            image=b64,
            type='base64',
        )

        data.update(params)
        return parse.urlencode(data).encode("utf-8")

    def send_image(self, image, send_params=dict(), additional_headers=dict()):
        """
        Main handler for sending images

            :params image -- Image object
            :params send_params -- additional info to be sent to imgur
            :params additional_headers -- additional headers to be added to request
        """
        req = request.Request(url=self._get_api(),
                              data=self._build_send_request(image, send_params),
                              headers=self._add_authorization_header(additional_headers)
                              )
        data = request.urlopen(req)
        return json.loads(data.read().decode("utf-8"))

    def delete_image(self, delete_hash, additional_headers=dict()):
        """
        Delete image from imgur

            :params delete_hash -- string containing unique
            image hash optained when sending an image
            :params additional_headers -- aditional headers to be addd to request
        """
        opener = request.build_opener(request.HTTPHandler)
        req = request.Request(url=self._get_api() + "/" + delete_hash,
                              headers=self._add_authorization_header(additional_headers))
        req.get_method = lambda: "DELETE"
        data = request.urlopen(req)
        return json.loads(data.read().decode("utf-8"))


imgur_handler = Imgur()
# image = request.files.get("my_image")
# image_data = imgur_handler.send_image(image)


class PhotoForm(FlaskForm):
    photo = FileField('Your photo')
    submit = SubmitField('upload')


@app.route('/', methods=('GET', 'POST'))
def upload():
    form = PhotoForm()
    if form.validate_on_submit():
        filename = secure_filename(form.photo.data.filename)
        image_data = imgur_handler.send_image(form.photo.data)
        print(image_data)
    return render_template(url_for("photo.html", form=form))

# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
#
#
# @app.route('/', methods=['GET', 'POST'])
# def upload():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         # if user does not select file, browser also
#         # submit a empty part without filename
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('uploaded_file',
#                                     filename=filename))
#     return '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#     <form action="" method=post enctype=multipart/form-data>
#       <p><input type=file name=file>
#          <input type=submit value=Upload>
#     </form>
#     '''
#
#
# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'],
#                                filename)


app.run()
