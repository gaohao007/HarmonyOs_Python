from flask import Flask, session,request,jsonify,render_template
import sqlite3
import os
from werkzeug.security import generate_password_hash,check_password_hash
from flask_jwt_extended  import  JWTManager,create_access_token,jwt_required,get_jwt_identity
from datetime import timedelta
import random
import  string

app = Flask(__name__)

# 配置JWT 秘钥
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
# 初始化JWT�化JWT = JWTManager()
jwt = JWTManager(app)

# 设置session密钥
app.secret_key = 'your-code-key'
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=4))




#配置数据库
DATABASE = 'database.db'
def init_db():
   if not os.path.exists(DATABASE):
       # 链接数据库db = SQLite3
       with sqlite3.connect(DATABASE) as conn:
           cursor = conn.cursor()
           #用户
           cursor.execute("""
               CREATED DATABASE
              """)
           cursor.execute('''
                  CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL,
                      password TEXT NOT NULL,
                      email TEXT NOT NULL
                  )
              ''')

           #轮播图片
           cursor.execute('''
                         CREATE TABLE IF NOT EXISTS carousel (
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             image_url TEXT NOT NULL,
                             title TEXT,
                             description TEXT
                         )
                     ''')
           conn.commit()


def add_images_to_carousel():
    image_folder = os.path.join(os.path.dirname(__file__),'static ','images')
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        print(f'Created image folder: {image_folder}')
        return

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for filename in os.listdir(image_folder):
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                image_path = os.path.join('static ','images', filename)
                title =os.patah.splitext(filename)[0]
                description = f'Description for {title}'
                cursor.execute("INSERT INTO carousel (image_url, title, description) VALUES (?, ?, ?)",
                                (image_path, title, description))
                conn.commit()
                print(f'Added image: {filename}')



@app.before_request
def create_tables():
    init_db()



@app.route("/get_verification_code", methods=["GET"])
def get_verification_code():
    code = generate_verification_code()
    session['verification_code'] = code
    return jsonify({'verification_code': code}), 200







@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not isinstance(data, dict) or not 'username' in data or not 'password' in data or not 'email' in data\
                or not 'verification_code' in data:
            return jsonify({'message': 'Missing required fields'}), 400
        username = data['username']
        password = data['password']
        email = data['email']
        verification_code = data['verification_code']

        # 验证验证码""
        stored_code = session.get('verification_code')
        if stored_code != verification_code:
            return jsonify({'message': 'Invalid verification code'}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? OR  email = ?", (username,email))
            existing_users = cursor.fetchone()
            if existing_users:
                return jsonify({'message': 'Username or email already exists'}), 400

        #     使用werkzeug.security 生成密码哈希
        hashed_password = generate_password_hash(password, method='pbkdf2:sha1')
        # 插入新用户到数据库
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                       (username, hashed_password, email))
        conn.commit()
        return jsonify({'message': 'Registration successful'}), 200
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500
# 登录接口
@app.route("/login", methods=["post"])
def login():
    try:
        data = request.get_json()
        if not isinstance(data, dict) or not 'username' in data or not 'password' in data:
            return jsonify({'message': 'Missing required files'}) ,400
        username = data['username']
        password = data['password']

        # 查询数据
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'Username does not exist'}), 401
            # 验证密码
            if not check_password_hash(user[2],password):
                 return jsonify({'message': 'Invalid password'}), 401

        # 生成访问令牌并设置有效时间
        expires = timedelta(days=2)
        access_token =  create_access_token(identity=username,expires_delta=expires)
        return jsonify({'message': 'Login successful','access_token':access_token}), 200
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route("/protected",methods=["GET"])
@jwt_required()
def protected():
    try:
        #获取当前用户的标识
        current_user = get_jwt_identity()
        return jsonify({'message':f'Hello {current_user}! This is a protected route.'}),200
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'message': 'Internal Server Error'}), 500

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True)
