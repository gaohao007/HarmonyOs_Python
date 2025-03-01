from flask import Flask, session,request,jsonify,render_template
import sqlite3
import os
from werkzeug.security import generate_password_hash,check_password_hash
from flask_jwt_extended  import  JWTManager,create_access_token,jwt_required,get_jwt_identity
from datetime import timedelta,datetime
import random
import  string


import smtplib
from email.mime.text import MIMEText


from werkzeug.utils import secure_filename

app = Flask(__name__)

# 配置JWT 秘钥
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
# 初始化JWT�化JWT = JWTManager()
jwt = JWTManager(app)

# 设置session密钥
app.secret_key = 'your-code-key'


def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

#配置数据库
DATABASE = 'database.db'
def init_db():

       # 链接数据库db = SQLite3
       with sqlite3.connect(DATABASE) as conn:
           cursor = conn.cursor()
           #用户
           cursor.execute('''
                  CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL,
                      password TEXT NOT NULL,
                      email TEXT NOT NULL
                  )
              ''')

           # 商品分类表   #自增主键id、分类名称name、图片路径image、父分类id（默认0实现层级结构）和排序序号（默认0控制显示顺序）
           cursor.execute('''
                     CREATE TABLE IF NOT EXISTS categories (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL,
                         image TEXT ,
                         parent_id INTEGER DEFAULT 0,
                         sort_order INTEGER DEFAULT 0  
                     )
                 ''')

           # SPU表（标准产品单元）
           cursor.execute('''
                        CREATE TABLE IF NOT EXISTS spu (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            description TEXT,
                            category_id INTEGER,
                            main_image TEXT,
                            detail_images TEXT,  
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (category_id) REFERENCES categories(id)
                        )
                    ''')

           # SKU表（库存单元）
           cursor.execute('''
                        CREATE TABLE IF NOT EXISTS sku (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            spu_id INTEGER NOT NULL,
                            price DECIMAL(10,2) NOT NULL,
                            stock INTEGER NOT NULL,
                            attrs TEXT, 
                            image TEXT,
                            status INTEGER DEFAULT 1,
                            FOREIGN KEY (spu_id) REFERENCES spu(id)
                        )
                    ''')

           # 商品属性表
           cursor.execute('''
               CREATE TABLE IF NOT EXISTS attributes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL UNIQUE, 
                   select_type INTEGER DEFAULT 1 
               )
           ''')



           # SPU-属性关联表
           cursor.execute('''
               CREATE TABLE IF NOT EXISTS spu_attribute (
                   spu_id INTEGER,
                   attribute_id INTEGER,
                   PRIMARY KEY (spu_id, attribute_id)
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
    session['verification_code_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
        stored_code_time_str = session.get('verification_code_time')
        if not stored_code or not stored_code_time_str:
            return jsonify({'message': 'Invalid verification code'}), 400
        stored_code_time = datetime.strptime(stored_code_time_str, '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()

        if (current_time - stored_code_time) > timedelta(minutes=5):
            return jsonify({'message': 'Verification code has expired'}), 400

        if stored_code != verification_code:
            return jsonify({'message': 'Invalid verification code'}), 400

        # 删除验证码，确保只能使用一次
        session.pop('verification_code', None)
        session.pop('verification_code_time', None)



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


@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 将结果转为字典格式
            cursor = conn.cursor()

            # 获取所有分类
            cursor.execute('''
                SELECT id, name, image, parent_id, sort_order 
                FROM categories 
                ORDER BY sort_order ASC
            ''')
            categories = [dict(row) for row in cursor.fetchall()]

            # 构建树形结构
            def build_tree(parent_id=0):
                return [
                    {
                        **category,
                        "children": build_tree(category['id'])
                    }
                    for category in categories
                    if category['parent_id'] == parent_id
                ]

            return jsonify({
                "code": 200,
                "data": build_tree(),
                "message": "Success"
            })

    except Exception as e:
        app.logger.error(f"获取分类失败: {str(e)}")
        return jsonify({
            "code": 500,
            "data": None,
            "message": "服务器内部错误"
        }), 500





































@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True)



























