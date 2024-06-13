from flask import Flask, render_template, request, jsonify
from models import initialize_database, create_user, create_user_profile, update_user_profile, create_user_image, create_user_with_details, get_users, get_user_details, get_user_by_id, get_user_details_by_id, update_user_profile, delete_user_by_id
from config import Config, DevelopmentConfig, ProductionConfig
from flask_cors import CORS
import os
from extensions import db
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# config_class='DevelopmentConfig'
config_class = os.getenv('FLASK_CONFIG', 'DevelopmentConfig')
app.config.from_object(f'config.{config_class}')

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    initialize_database()

#REGISTER OR CREATE AN USER
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')  
    email = data.get('email')
    try:
        user_id = create_user(username, password, email)
        return jsonify({"message": "User created successfully", "user_id": user_id}), 201
    except Exception as e:
        # Handle errors and conflicts, such as a duplicate username
        return jsonify({"error": "User creation failed", "details": str(e)}), 400

#CREATE AN USER PROFILE WITH USER ID
@app.route('/user_profile/<int:user_id>', methods=['POST'])
def create_user_profile_by_id(user_id):
    data = request.get_json()
    profile_data = data.get('profile')    
    try:
        # Call your model function to create the user with details
        user_id = create_user_profile(user_id, profile_data)
        return jsonify({"message": "User Profile created successfully", "profile_id": user_id}), 201
    except Exception as e:
        # In a real application, you might want to log this error and return a more generic error message
        return jsonify({"error": "Failed to create user", "details": str(e)}), 400

#CREATE AN USER IMAGE WITH USER ID
@app.route('/user_image', methods=['POST'])
def create_user_image_by_id():
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['image']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Assuming you have a model to save details in the database
        # You will also need to collect other form data (e.g., username, email)
        # user_details = {
        #     'username': request.form.get('username'),
        #     'email': request.form.get('email'),
        #     'image_path': filepath
        # }
        image_url = filepath
        user_id = request.form.get('user_id')
  
    try:
        # Call your model function to create the image with user_id
        image_id = create_user_image(user_id, image_url)
        return jsonify({"message": "User Image created successfully", "image_id": image_id}), 201
    except Exception as e:
        # In a real application, you might want to log this error and return a more generic error message
        return jsonify({"error": "Failed to create image", "details": str(e)}), 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#GET USER WITH USER ID    
@app.route('/user/<int:user_id>', methods=['GET'])
def user_by_id(user_id):
    user = get_user_by_id(user_id)
    if user:
        return jsonify(user)
    else:
        return jsonify({"error": "User not found"}), 404
 
#GET USER DETAILS WITH USER ID
@app.route('/user_details/<int:user_id>', methods=['GET'])
def user_details_by_id(user_id):
    user = get_user_details_by_id(user_id)
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404

#UPDATE USER WITH USER ID
# @app.route('/user/<int:user_id>', methods=['PUT'])
# def update_user(user_id):
#     data = request.get_json()
#     user = update_user(user_id, data['username'], data['email'])
#     if user:
#         return jsonify(user)
#     else:
#         return jsonify({"error": "User not found"}), 404

#UPDATE USER PROFILE WITH USER ID
@app.route('/user_profile/<int:user_id>', methods=['PUT'])
def update_user_details(user_id):
    data = request.get_json()
    profile_data = data.get('profile')  
    user = update_user_profile(user_id, profile_data['first_name'], profile_data['last_name'], profile_data['contact_no'], profile_data['dob'], profile_data['bio'], profile_data['country'])
    if user:
        return jsonify(user)
    else:
        return jsonify({"error": "User not found"}), 404

#DELETE USER WITH USER ID    
@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # pass
    user = delete_user_by_id(user_id)
    if user:
        # return jsonify(user)
        return jsonify({"message": "User ID " + str(user['user_id']) + " has been deleted successfully"}), 201
    else:
        return jsonify({"error": "User not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1")
