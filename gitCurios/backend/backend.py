from pathlib import Path
import modal
from modal_image import image, stub
from modal import web_endpoint, Volume
import os
import shlex
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify
import modal


app = Flask(__name__)

@app.route('/api', methods=['POST'])
def handle_request():
    data = request.json
    # Process the request...
    response = {'message': 'Processed data', 'input': data}
    return jsonify(response)

def run_flask_app():
    app.run(host='0.0.0.0', port=5000)

# Define the path to the local Streamlit script
streamlit_script_local_path = Path(__file__).parent / "chatbot_front.py"
streamlit_script_remote_path = Path("/root/chatbot_front.py")

# Ensure the Streamlit script exists locally
if not streamlit_script_local_path.exists():
    raise RuntimeError("streamlit.py not found! Place the script in the same directory.")

# Create a mount for the Streamlit script
streamlit_script_mount = modal.Mount.from_local_file(
    streamlit_script_local_path, streamlit_script_remote_path)

@stub.function(image=image, mounts=[streamlit_script_mount])
@modal.web_server(8000)
def run_streamlit():
    target = shlex.quote(str(streamlit_script_remote_path))
    cmd = f"streamlit run {target} --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false"
    subprocess.Popen(cmd, shell=True)

@stub.function(image=image)
@modal.web_server(5000)
def serve_flask():
    run_flask_app()


volume = Volume.from_name(
    "repo_data", create_if_missing=True
)

MODEL_DIR = "/model"


@stub.local_entrypoint()
def run() :
    run_streamlit()
    serve_flask()

