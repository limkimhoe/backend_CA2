# auth.py
from functools import wraps
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from flask import jsonify

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # verify_jwt_in_request()  # Ensure the JWT is present and valid
        # current_user = get_jwt_identity()  # Assuming the identity is the user ID
        
        user_role = get_user_role_from_jwt()
        print('role:'+user_role)
        
        if user_role != 'admin':
            return jsonify({"msg": "Administration privileges required."}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def get_user_role_from_jwt():
    claims = get_jwt()
    print(claims)
    jwt_role = None
    if 'role' in claims:
        jwt_role =  claims['role']
    else:
        None
    return jwt_role
    # return claims['role'] if 'role' in claims else None
