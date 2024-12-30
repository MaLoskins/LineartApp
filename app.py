from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import os
import uuid
import time
import random
from threading import Lock

from Lineart import call_lineart

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.abspath(os.getcwd())
INPUT_DIR = os.path.join(BASE_DIR, "input", "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "images")
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

processing_lock = Lock()

def is_file_accessible(filepath, mode='rb'):
    """Check if a file is accessible with the given mode."""
    try:
        with open(filepath, mode):
            return True
    except IOError:
        return False

def wait_for_file(filepath, timeout=60, check_interval=0.5):
    """
    Wait until the file exists and is accessible.
    Returns True if the file is accessible within the timeout, False otherwise.
    """
    start_time = time.time()
    while True:
        if os.path.exists(filepath) and is_file_accessible(filepath):
            return True
        if time.time() - start_time > timeout:
            return False
        time.sleep(check_interval)

def rename_with_retry(src_path, dst_path, max_retries=5, delay=1.0):
    """
    Attempt to rename a file with retry logic. Sleep if sharing violation occurs.
    Returns True on success, False on repeated failure.
    """
    for attempt in range(max_retries):
        try:
            os.rename(src_path, dst_path)
            return True
        except PermissionError as e:
            # WinError 32 -> file is in use by another process
            if attempt < max_retries - 1:
                print(f"Rename failed due to permission error. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"Rename failed after {max_retries} attempts: {e}")
                return False
        except OSError as e:
            print(f"Unexpected error during rename: {e}")
            return False
    return False

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in the request'}), 400
    if 'prompt' not in request.form:
        return jsonify({'error': 'No prompt provided'}), 400

    image = request.files['image']
    prompt = request.form['prompt']

    if image.filename == '':
        return jsonify({'error': 'No selected image'}), 400

    try:
        with processing_lock:
            unique_id = uuid.uuid4().hex
            original_filename = f"Temp_{unique_id}.png"
            image_path = os.path.join(INPUT_DIR, original_filename)
            image.save(image_path)

            seed = random.randint(100000000000000, 999999999999999)

            # Call your lineart function (this calls ComfyUI in the background)
            call_lineart(OUTPUT_DIR, prompt, image_path, seed)

            edited_image_source_path = os.path.join(OUTPUT_DIR, 'image.png')
            if not wait_for_file(edited_image_source_path):
                return jsonify({'error': 'Processing timed out. Edited image not found.'}), 500

            edited_unique_filename = f"image_{unique_id}.png"
            edited_image_destination_path = os.path.join(OUTPUT_DIR, edited_unique_filename)

            success = rename_with_retry(edited_image_source_path, edited_image_destination_path)
            if not success:
                return jsonify({'error': 'File is in use and cannot be renamed after several retries.'}), 500

            # Remove original file to save space
            try:
                os.remove(image_path)
            except OSError:
                pass

            edited_image_url = f'/static/images/{edited_unique_filename}'
            return jsonify({'editedImageUrl': edited_image_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/images/<filename>')
def serve_image(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    # Make sure you see something like this at the bottom.
    # If the console is instantly closing, run it from CMD:
    #   python app.py
    # so you can read the traceback if it crashes.
    app.run(host='0.0.0.0', port=5000, debug=True)
