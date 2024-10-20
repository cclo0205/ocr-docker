# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, send_from_directory, jsonify
from flask_restful import Api
from loguru import logger
import base64, os
import pytesseract
import subprocess
import time
from io import BytesIO
#from PIL import Image

try:
    from PIL import Image
except ImportError:
    import Image


# Validating file extension
def allowed_file(image_file):
    logger.info("Validating file extension")
    return '.' in image_file and \
           image_file.rsplit('.', 1)[1].lower() in "png,jpg,pdf,tiff"

# Getting file extension
def getExtention(image_file):
    logger.info("Getting file extension")
    filename, file_extension = os.path.splitext(image_file)
    return filename, file_extension

def convert_to_tiff(image_file):
    logger.info("Converting pdf to tiff")
    converted_file_name = image_file.replace('pdf','tiff')
    p = subprocess.Popen('convert -density 300 '+ image_file +' -background white -alpha Off '+ converted_file_name , stderr=subprocess.STDOUT, shell=True)
    p_status = p.wait()
    time.sleep(5)
    if os.path.exists(image_file):
        os.remove(image_file)
    return converted_file_name


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "/opt/ocr/tmp"
api = Api(app)

@app.route('/ocr', methods=['POST'])
def ocr():
    if request.method == 'POST':
        # Check if the request contains JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        language = data.get('languages')
        base64_image = data.get('image')

        if not base64_image:
            return "Data posted does not contain a base64 image"
        if not language:
            return "Please select OCR Language"

        try:
            # Decode the base64 image
            image_data = base64.b64decode(base64_image)
            image = Image.open(BytesIO(image_data))
        except Exception as e:
            return f"Invalid image data: {e}"
        
        #return image.format
        #image.save('/opt/ocr/tmp/your_image.png', format='PNG')


        # Perform OCR on the decoded image
        config = "--psm 7"
        if image.format.lower() == 'tiff':
            txt = ''
            for frame in range(image.n_frames):
                image.seek(frame)
                txt += pytesseract.image_to_string(image, config=config, lang=language) + '\n'
            return jsonify({"text": txt}), 200
        else:
            txt = pytesseract.image_to_string(image, lang=language, config=config)
            return jsonify({"text": txt.strip()}), 200



@app.route('/')
def devices():
    return render_template('index.html')


@app.route('/languages')
def languages():
    return jsonify(pytesseract.get_languages())

# Serve Javascript
@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)




# Start Application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
