from functools import wraps
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from flask import jsonify

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()  # Ensure the JWT is present and valid
        current_user = get_jwt_identity()  # Assuming the identity is the user ID
        
        # You need to implement get_user_role. It should return the role of the user
        # based on current_user, which could involve querying your database.
        user_role = get_user_role_from_jwt()
        print('role:'+user_role)
        
        if user_role != 'admin':
            return jsonify({"msg": "Administration privileges required."}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def get_user_role_from_jwt():
    claims = get_jwt()
    print(claims)
    return claims['role'] if 'role' in claims else None


# def get_user_role(user_id):
#     # Assuming you have a User model with a role attribute
#     user = User.query.filter_by(id=user_id).first()
#     return user.role if user else None

