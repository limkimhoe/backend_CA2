from extensions import db, bcrypt
from sqlalchemy import text, exc
from flask_jwt_extended import create_access_token
import pandas as pd
import csv


def create_user_tables():
    user_table_sql = text("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(64) NOT NULL, 
            email VARCHAR(120) UNIQUE NOT NULL
        )ENGINE=InnoDB;
    """)

    user_profile_table_sql = text("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            first_name VARCHAR(100) NULL,
            last_name VARCHAR(100) NULL,
            contact_no VARCHAR(15),
            dob DATE NULL,
            bio TEXT,
            country VARCHAR(100) NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )ENGINE=InnoDB; 
    """)

    image_table_sql = text("""
        CREATE TABLE IF NOT EXISTS images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            image_url VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )ENGINE=InnoDB; 
    """)

    role_table_sql = text("""
    CREATE TABLE IF NOT EXISTS roles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(80) UNIQUE NOT NULL,
        description TEXT
    )ENGINE=InnoDB; 
    """)

    user_roles_table_sql = text("""
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INT NOT NULL,
        role_id INT NOT NULL,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
    )ENGINE=InnoDB; 
    """)

    roles = ['admin', 'standard']
    insert_role_sql = text("""
         INSERT INTO roles (name) VALUES (:name) ON DUPLICATE KEY UPDATE name = name;
    """)

    with db.engine.begin() as connection:
        connection.execute(user_table_sql)
        connection.execute(user_profile_table_sql)
        connection.execute(image_table_sql)
        connection.execute(image_table_sql)
        connection.execute(user_roles_table_sql)
        # The transaction is committed here when the block exits
        
        for role_name in roles:
            connection.execute(insert_role_sql, {'name': role_name})

def initialize_database():
    """Create user tables if they don't exist before the first request."""
    create_user_tables()


### CRUD USER ###
#CREATE USER
def create_user(username, password, email, role_id):
    try:

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password

        # Insert into users table
        user_sql = text("""
        INSERT INTO users (username, password, email) 
        VALUES (:username, :password, :email);
        """)
        
        # Execute the query
        db.session.execute(user_sql, {'username': username, 'password': hashed_password, 'email': email})

        # Fetch the ID of the last inserted row
        user_id = db.session.execute(text('SELECT LAST_INSERT_ID();')).fetchone()[0]

        assign_role_sql = text("""
            INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id);
            """)
            
        db.session.execute(assign_role_sql,{'user_id': user_id, 'role_id': role_id})
        
        db.session.commit()
        return user_id
    
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e   
    
def create_user_image(user_id, image_url):
    try:
        # Insert into user_profiles table
        image_sql = text("""
        INSERT INTO images (user_id, image_url) VALUES (:user_id, :image_url)
        """)
        db.session.execute(image_sql, {'user_id': user_id,'image_url':image_url})
        user_image_id = db.session.execute(text('SELECT LAST_INSERT_ID();')).fetchone()[0]        
        db.session.commit()
        return user_image_id
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e

#CREATE USER PROFILE
def create_user_profile(user_id, profile_data):
    
    try:
        # Insert into user_profiles table
        profile_sql = text("""
        INSERT INTO user_profiles (user_id, first_name, last_name, contact_no, dob, bio, country) VALUES (:user_id, :first_name, :last_name, :contact_no, :dob, :bio, :country)
        """)
        db.session.execute(profile_sql, {**profile_data, 'user_id': user_id})
        user_profile_id = db.session.execute(text('SELECT LAST_INSERT_ID();')).fetchone()[0]        
        db.session.commit()
        return user_profile_id
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e

def get_user_by_id(user_id):
    try:
        sql = text("SELECT id, username, email FROM users WHERE id = :user_id;")
        result = db.session.execute(sql, {'user_id': user_id})
        user = result.fetchone()

        # No need to commit() as no changes are being written to the database
        if user:
            # Convert the result into a dictionary if not None
            user_details = user._asdict()
            return user_details
        else:
            return None
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e

def get_user_details_by_id(user_id):
    try:
        sql = text("""
        SELECT 
            users.id as user_id, 
            users.username, 
            users.email, 
            user_profiles.first_name, 
            user_profiles.last_name, 
            user_profiles.contact_no, 
            user_profiles.dob, 
            user_profiles.bio, 
            user_profiles.country,
            GROUP_CONCAT(images.image_url) as image_urls
        FROM 
            users
        LEFT JOIN 
            user_profiles ON users.id = user_profiles.user_id
        LEFT JOIN 
            images ON users.id = images.user_id
        WHERE users.id = :user_id
        GROUP BY 
            users.id, 
            user_profiles.id;
        """)
        result = db.session.execute(sql, {'user_id': user_id})
        user_details = result.fetchone()
        return user_details._asdict() if user_details else None
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e

def update_user_profile(user_id, first_name, last_name, contact_no, dob, bio, country):
    try:
        sql = text("UPDATE user_profiles SET first_name = :first_name, last_name = :last_name, contact_no = :contact_no, dob = :dob, bio = :bio, country = :country WHERE user_id = :user_id;")
        result = db.session.execute(sql, {'user_id': user_id, 'first_name': first_name, 'last_name': last_name, 'contact_no': contact_no, 'dob': dob, 'bio': bio, 'country': country})
        db.session.commit()
        print(result.rowcount)
        if result.rowcount > 0:
            # Convert the result into a dictionary if not None
            # user_details = result._asdict()
            return {"user_id": user_id}
        else:
            return None

    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e

def create_user_with_details(username, password, email, profile_data, image_urls):
    pass

def get_users():
    sql = 'SELECT id, username, email FROM users;'
    result = db.session.execute(sql)
    users = [dict(row) for row in result]
    return users



def get_user_details():
    sql = text("""
    SELECT 
        users.id as user_id, 
        users.username, 
        users.email, 
        user_profiles.first_name, 
        user_profiles.last_name, 
        user_profiles.contact_no, 
        user_profiles.dob, 
        user_profiles.bio, 
        user_profiles.country, 
        GROUP_CONCAT(images.image_url) as image_urls
    FROM 
        users
    LEFT JOIN 
        user_profiles ON users.id = user_profiles.user_id
    LEFT JOIN 
        images ON users.id = images.user_id
    GROUP BY 
        users.id, 
        user_profiles.id;
    """)
    result = db.session.execute(sql)
    user_details = [row._asdict() for row in result]
    return user_details

def delete_user_by_id(user_id):
    try:
        sql_delete_profile = text("""
        DELETE FROM user_profiles
        WHERE user_profiles.user_id = :user_id;
        """)
        sql_delete_user = text("""
        DELETE FROM users                       
        WHERE users.id = :user_id;
        """)
        result1 = db.session.execute(sql_delete_profile, {'user_id': user_id})
        result2 = db.session.execute(sql_delete_user, {'user_id': user_id})
        db.session.commit()
        # delete_1 = result1.fetchone()
        return {'user_id':user_id}
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e
    

def authenticate_user(username, password):
    # hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password

    sql = text('SELECT id, password FROM users WHERE username = :username;')
    result = db.session.execute(sql, {'username': username})
    user = result.mappings().first()  # This gives you a dict-like object

    print(user)
    
    if user and bcrypt.check_password_hash(user['password'], password):
        return user['id']  # Authentication successful
    else:
        return None  # Authentication failed


def authenticate_user_jwt(username, password):
    # hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password

    sql = text("""
    SELECT users.id as user_id, users.password as password, roles.name as role FROM 
        users 
    LEFT JOIN 
        user_roles ON users.id = user_roles.user_id
    LEFT JOIN 
        roles ON user_roles.role_id = roles.id  
        WHERE username = :username;
    """)
    result = db.session.execute(sql, {'username': username})
    user = result.mappings().first()  # This gives you a dict-like object

    print('role:'+ user['role'])
    print('role:'+ user['role'])
    
    if user and bcrypt.check_password_hash(user['password'], password):
        # Create JWT token if authentication is successful
        access_token = create_access_token(identity=str(user['user_id']), additional_claims={"role": user['role']})
        access_token = create_access_token(identity=str(user['user_id']), additional_claims={"role": user['role']})
        return access_token  # Return the JWT token
    else:
        return None  # Authentication failed
    



def csv_to_json(file_path):
    # Read CSV file into DataFrame
    df = pd.read_csv(file_path)
    
    # Convert DataFrame to JSON
    json_data = df.to_json(orient='records', indent=4)
    
    return json_data

def csv_to_dict_list(file_path):
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        data = {}
        for row in csv_reader:
            for column, value in row.items():
                data.setdefault(column, []).append(value)
    return data