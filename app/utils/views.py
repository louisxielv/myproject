import os

from flask import request, url_for, make_response, current_app

from . import utils
from .tools import gen_rnd_filename
from .. import csrf
from ..recipes.forms import PhotoForm
from werkzeug.utils import secure_filename

#
# @app.route('/upload/', methods=('GET', 'POST'))
# def upload():
#     form = PhotoForm()
#     if form.validate_on_submit():
#         filename = secure_filename(form.photo.data.filename)
#         form.photo.data.save('uploads/' + gen_rnd_filename(filename))
#     else:
#         filename = None
#     return True


@csrf.exempt
@utils.route('/ckupload/', methods=['POST', 'OPTIONS'])
def ckupload():
    """CKEditor file upload"""
    error = ''
    url = ''
    callback = request.args.get("CKEditorFuncNum")

    if request.method == 'POST' and 'upload' in request.files:
        fileobj = request.files['upload']
        rnd_name = gen_rnd_filename(fileobj.filename)

        filepath = os.path.join(current_app.static_folder, 'upload', rnd_name)

        # 检查路径是否存在，不存在则创建
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                error = 'ERROR_CREATE_DIR'
        elif not os.access(dirname, os.W_OK):
            error = 'ERROR_DIR_NOT_WRITEABLE'

        if not error:
            fileobj.save(filepath)
            url = url_for('static', filename='%s/%s' % ('upload', rnd_name))
    else:
        error = 'post error'

    res = """<script type="text/javascript">
  window.parent.CKEDITOR.tools.callFunction(%s, '%s', '%s');
</script>""" % (callback, url, error)

    response = make_response(res)
    response.headers["Content-Type"] = "text/html"
    return response

# Snoopyimage.jpg
# < FileStorage: 'Snoopyimage.jpg'('image/jpeg') >
# {'data': {'nsfw': None, 'views': 0, 'description': None, 'width': 736, 'section': None, 'height': 736,
#           'datetime': 1480722776, 'deletehash': 'lLj6ZGy6xrtz8n7', 'size': 38900, 'bandwidth': 0, 'id': '57tyrKT',
#           'link': 'http://i.imgur.com/57tyrKT.jpg', 'animated': False, 'is_ad': False, 'type': 'image/jpeg',
#           'account_url': None, 'vote': None, 'in_gallery': False, 'account_id': 0, 'name': '', 'favorite': False,
#           'title': None}, 'status': 200, 'success': True}
