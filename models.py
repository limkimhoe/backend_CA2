from extensions import db, bcrypt
from sqlalchemy import text, exc
from flask_jwt_extended import create_access_token

def create_user_tables():
    users_table_sql = text("""
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

    images_table_sql = text("""
        CREATE TABLE IF NOT EXISTS images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            image_name VARCHAR(100) NOT NULL,
            image_url VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )ENGINE=InnoDB; 
    """)

    user_image_table_sql = text("""
    CREATE TABLE IF NOT EXISTS user_image (
        user_id INT NOT NULL,
        image_id INT NOT NULL,
        PRIMARY KEY (user_id, image_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
    )ENGINE=InnoDB; 
    """)

    roles_table_sql = text("""
    CREATE TABLE IF NOT EXISTS roles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(80) UNIQUE NOT NULL,
        description TEXT
    )ENGINE=InnoDB; 
    """)

    user_role_table_sql = text("""
    CREATE TABLE IF NOT EXISTS user_role (
        user_id INT NOT NULL,
        role_id INT NOT NULL,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
    )ENGINE=InnoDB; 
    """)

    # roles = ['admin', 'standard']
    # insert_role_sql = text("""
    #      INSERT INTO roles (name) VALUES (:name) ON DUPLICATE KEY UPDATE name = name;
    # """)

    with db.engine.begin() as connection:
        connection.execute(users_table_sql)
        connection.execute(user_profile_table_sql)
        connection.execute(images_table_sql)
        connection.execute(user_image_table_sql)
        connection.execute(roles_table_sql)
        connection.execute(user_role_table_sql)
        # The transaction is committed here when the block exits
        
        # for role_name in roles:
        #     connection.execute(insert_role_sql, {'name': role_name})

def initialize_database():
    """Create user tables if they don't exist before the first request."""
    create_user_tables()


### CRUD USER ###
#CREATE USER
def create_user(username, password, email, role_name):
    try:

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password
        print(hashed_password)
        # Insert into users table
        user_sql = text("""
        INSERT INTO users (username, password, email) 
        VALUES (:username, :password, :email);
        """)
        
        # Execute the query
        db.session.execute(user_sql, {'username': username, 'password': hashed_password, 'email': email})

        # Fetch the ID of the last inserted row
        user_id = db.session.execute(text('SELECT LAST_INSERT_ID();')).fetchone()[0]

        get_role_id_sql = text("""
            SELECT id FROM roles WHERE roles.name = :role_name;
            """)
        
        result = db.session.execute(get_role_id_sql,{'role_name': role_name})
        role = result.fetchone()
        role_id = role[0]

        print(role_id)

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
    
def create_user_image(user_id, image_name, image_url):
    try:

        print(image_name, image_url)
        # Insert into user_profiles table
        image_sql = text("""
        INSERT INTO images (image_name, image_url) VALUES (:image_name, :image_url)
        """)

        # Execute the query
        db.session.execute(image_sql, {'image_name': image_name, 'image_url':image_url})

        # Fetch the ID of the last inserted row
        image_id = db.session.execute(text('SELECT LAST_INSERT_ID();')).fetchone()[0]

        assign_image_sql = text("""
            INSERT INTO user_image (user_id, image_id) VALUES (:user_id, :image_id);
            """)
        db.session.execute(assign_image_sql, {'user_id': user_id, 'image_id': image_id})

        # user_image_id = db.session.execute(text('SELECT LAST_INSERT_ID();')).fetchone()[0]        
        db.session.commit()
        return image_id
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
            users.status,
            user_profiles.first_name, 
            user_profiles.last_name, 
            user_profiles.contact_no, 
            user_profiles.dob, 
            user_profiles.bio, 
            user_profiles.country,
            roles.name as role_name,
            GROUP_CONCAT(images.image_name) as image_names,
            GROUP_CONCAT(images.image_url) as image_urls
        FROM 
            users
        LEFT JOIN 
            user_profiles ON users.id = user_profiles.user_id
        LEFT JOIN 
            user_image ON users.id = user_image.user_id 
        LEFT JOIN
            images ON user_image.image_id = images.id
        LEFT JOIN 
            user_roles ON users.id = user_roles.user_id 
        LEFT JOIN
            roles ON user_roles.role_id = roles.id
        WHERE users.id = :user_id
        GROUP BY 
            users.id, 
            user_profiles.id,
            roles.id;
        """)
        result = db.session.execute(sql, {'user_id': user_id})
        user_details = result.fetchone()
        return user_details._asdict() if user_details else None
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e

def update_user(user_id, update_data):
    try:
        update_clauses = []
        params = {}
        attr = ['password', 'email', 'status']
        for key, value in update_data.items():
            if key in attr:  # Ensure the key is an attribute of the User model
                update_clauses.append(f"{key} = :{key}")
                params[key] = value

        if not update_clauses:
            return {'error': 'No valid fields provided for update'}

        params['user_id'] = user_id
        sql = text(f"UPDATE users SET {', '.join(update_clauses)} WHERE id = :user_id")
        result = db.session.execute(sql, params)
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


def create_role(role_name, description):

    try:
        sql = text(""" INSERT INTO user_profiles (role_name, description) VALUES (:role_name, :description) """)
        result = db.session.execute(sql, {'role_name': role_name, 'description': description})
        role_id = db.session.execute(text('SELECT LAST_INSERT_ID();')).fetchone()[0]        
        db.session.commit()
        return role_id
    
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e
 
def get_role_by_id(role_id):
    try:
        sql = text("SELECT id, role_name, description FROM roles WHERE id = :role_id;")
        result = db.session.execute(sql, {'role_id': role_id})
        role = result.fetchone()

        # No need to commit() as no changes are being written to the database
        if role:
            # Convert the result into a dictionary if not None
            role_details = role._asdict()
            return role_details
        else:
            return None
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e
 
def update_role_by_id(role_id, role_name):
    try:
        sql = text("UPDATE roles SET role_name = :role_name WHERE role_id = :id;")
        result = db.session.execute(sql, {'id': role_id, 'role_name': role_name})
        db.session.commit()

        if result.rowcount > 0:
            # Convert the result into a dictionary if not None
            return {"role_id": role_id}
        else:
            return None

    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e
 
def delete_role_by_id(role_id):
    try:
        sql_delete_role = text("""
        DELETE FROM roles
        WHERE roles.role_id = :id;
        """)

        result = db.session.execute(sql_delete_role, {'id': role_id})

        db.session.commit()

        return {'role_id':role_id}
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e



def get_users():
    sql = 'SELECT id, username, email FROM users;'
    result = db.session.execute(sql)
    users = [dict(row) for row in result]
    return users


def get_user_details(per_page, offset):
    print(per_page, offset)
    try:
        sql = text("""
        SELECT 
            users.id as user_id, 
            users.username, 
            users.email, 
            users.status,
            user_profiles.first_name, 
            user_profiles.last_name, 
            user_profiles.contact_no, 
            user_profiles.dob, 
            user_profiles.bio, 
            user_profiles.country,
            GROUP_CONCAT(images.image_name) as image_names,
            GROUP_CONCAT(images.image_url) as image_urls
        FROM 
            users
        LEFT JOIN 
            user_profiles ON users.id = user_profiles.user_id
        LEFT JOIN 
            user_image ON users.id = user_image.user_id 
        LEFT JOIN
            images ON user_image.image_id = images.id
        GROUP BY 
            users.id, 
            user_profiles.id
        ORDER BY 
            users.id
        LIMIT :per_page OFFSET :offset;
        """)
        result = db.session.execute(sql, {'per_page':per_page, 'offset': offset })
        # user_details = result.fetchone()
        # return user_details._asdict() if user_details else None
        results = result.fetchall()
        keys = result.keys()  # This fetches the column names
        list_of_dicts = [dict(zip(keys, row)) for row in results]
        # print(result)
        # list_of_dicts = [dict(row) for row in result.mappings()]
        return list_of_dicts
    except Exception as e:
        # Rollback the transaction in case of error
        db.session.rollback()
        raise e

def delete_user_by_id(user_id):
    try:
        sql_delete_user = text("""
        UPDATE users SET status = 2                       
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

def hard_delete_user_by_id(user_id):
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

    if user:
        if bcrypt.check_password_hash(user['password'], password):
            return user['id']  # Authentication successful
        else:
            return None  # Authentication failed
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
    if user:
        print('role:'+ user['role'])
        # print('role:'+ user['role'])
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password
        print(hashed_password)

        if bcrypt.check_password_hash(user['password'], password):
            # Create JWT token if authentication is successful
            # access_token = create_access_token(identity=str(user['user_id']), additional_claims={"role": user['role']})
            access_token = create_access_token(identity=str(user['user_id']), additional_claims={"role": user['role']})
            return access_token  # Return the JWT token
        else:
            return None  
            # Authentication failed
    else:
        return None  
        # Authentication failed