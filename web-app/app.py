import os
import subprocess
import platform
from flask import Flask, render_template, request, Response

app = Flask(__name__)

# --- Universal Directory Mapping ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERRAFORM_DIR = os.path.join(BASE_DIR, "terraform")

def get_tf_command(user_intent):
    """Detects OS and builds the correct Terraform command."""
    is_windows = platform.system() == "Windows"
    
    # Use standard terraform command (ensure it's in your PATH on ada)
    tf_bin = "terraform"
    
    # Build -var flags dynamically from the UI form inputs
    var_flags = ""
    for key, value in user_intent.items():
        if is_windows:
            var_flags += f" -var=\"{key}={value}\""
        else:
            var_flags += f" -var='{key}={value}'"

    return f"{tf_bin} init && {tf_bin} apply -auto-approve{var_flags}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/provision', methods=['POST'])
def provision():
    # Capture all form inputs as a dictionary
    user_intent = request.form.to_dict()

    def generate():
        yield "🚀 Intent Received. Preparing Terraform variables...\n"
        full_cmd = get_tf_command(user_intent)
        
        yield f"💻 System: {platform.system()} | Overrides: {len(user_intent)}\n"
        yield "--------------------------------------------------\n"
        
        process = subprocess.Popen(
            full_cmd,
            cwd=TERRAFORM_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True
        )
        
        for line in process.stdout:
            yield line
        
        return_code = process.wait()
        
        if return_code == 0:
            yield "\n✅ Infrastructure lifecycle completed successfully."
        else:
            yield f"\n❌ Terraform failed (Exit Code: {return_code})."

    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    # Ready for Ada server
    app.run(debug=True, host='0.0.0.0', port=5000)
