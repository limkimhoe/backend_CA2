from flask import Flask, render_template, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import initialize_database, create_user, create_user_profile, update_user_profile, create_user_image, create_user_with_details, get_users, get_user_details, get_user_by_id, get_user_details_by_id, update_user_profile, delete_user_by_id, authenticate_user, authenticate_user_jwt, csv_to_dict_list, csv_to_json
from config import Config, DevelopmentConfig, ProductionConfig
from flask_cors import CORS
import os, json
from extensions import db
from werkzeug.utils import secure_filename

jwt = JWTManager()

app = Flask(__name__)
CORS(app)

# config_class='DevelopmentConfig'
config_class = os.getenv('FLASK_CONFIG', 'DevelopmentConfig')
app.config.from_object(f'config.{config_class}')

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
jwt.init_app(app)

with app.app_context():
    initialize_database()

#REGISTER OR CREATE AN USER
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')  
    email = data.get('email')
    role_id = data.get('role_id')
    try:
        user_id = create_user(username, password, email, role_id)
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


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user_id = authenticate_user(username, password)
    
    if user_id:
        # For simplicity, returning a message; in a real app, consider returning a token
        return jsonify({'message': 'Login successful', 'user_id': user_id}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401


@app.route('/login-jwt', methods=['POST'])
def loginjwt():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    # Attempt to authenticate the user
    access_token = authenticate_user_jwt(username, password)
    
    if access_token:
        # If authentication is successful, return the access token
        return jsonify(access_token=access_token), 200
    else:
        # If authentication fails, return an error message
        return jsonify({"msg": "Bad username or password"}), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/get_csv', methods=['GET'])
def get_csv():
    file_path = "static/data/hdb_resale_sample_raw.csv"
    data = csv_to_dict_list(file_path)
    return json.dumps(data, indent=4)

@app.route('/get_csv_pandas', methods=['GET'])
def get_csv_pandas():
    file_path = "static/data/hdb_resale_sample_raw.csv"
    data = csv_to_json(file_path)
    return data


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1")
