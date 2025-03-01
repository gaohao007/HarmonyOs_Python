from flask import Flask, session,request,jsonify,render_template
import sqlite3
import os
from werkzeug.security import generate_password_hash,check_password_hash
from flask_jwt_extended  import  JWTManager,create_access_token,jwt_required,get_jwt_identity
from datetime import timedelta,datetime
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
           # 创建SPU表结构，包含以下字段：
           # - id: 自增主键
           # - name: 产品名称（非空约束）
           # - description: 产品描述
           # - category_id: 关联分类表的分类ID（外键约束）
           # - main_image: 主图存储路径
           # - detail_images: 详情图路径列表（以特定格式存储）
           # - created_at: 记录创建时间（自动填充时间戳）
           # 外键约束确保category_id必须存在于categories表的id字段
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

           # 创建SKU数据表，用于存储商品库存单位信息
           # 表结构说明：
           #   id: 主键，自增唯一标识
           #   spu_id: 关联的SPU商品ID，不可为空
           #   price: 商品价格，保留两位小数
           #   stock: 库存数量
           #   combination: 规格组合值（如颜色+尺寸），作为唯一约束组成部分
           #   image: 商品展示图路径（可选）
           #   status: 商品状态，默认1表示可用
           # 约束说明：
           #   唯一约束：同一SPU下不能有重复规格组合
           #   外键约束：spu_id关联SPU表的id字段
           cursor.execute('''
               CREATE TABLE IF NOT EXISTS sku (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   spu_id INTEGER NOT NULL,
                   price DECIMAL(10,2) NOT NULL,
                   stock INTEGER NOT NULL,
                   combination TEXT NOT NULL,
                   image TEXT,
                   status INTEGER DEFAULT 1,
                   UNIQUE(spu_id, combination), 
                   FOREIGN KEY (spu_id) REFERENCES spu(id)
               )
           ''')

           # 商品属性表
          # 创建商品属性表（attribute），
          #  用于存储商品属性信息  参数: cursor: 数据库游标对象，用于执行SQL语句  表结构说明:
          #  1. id - 主键，自增长
          #  2. name - 属性名称，非空
          #  3. input_type - 输入类型，整型，取值范围为1、2、3
          #  4. is_required - 是否必填，默认0（非必填）
          #  5. category_id - 所属分类ID，外键关联categories表
          #  6. sort_order - 排序序号，默认0
          #  7. is_filterable - 是否可筛选，默认0（不可筛选）
           cursor.execute('''
               CREATE TABLE IF NOT EXISTS attribute (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   input_type INTEGER NOT NULL CHECK(input_type IN (1,2,3)), 
                   is_required INTEGER DEFAULT 0,
                   category_id INTEGER,
                   sort_order INTEGER DEFAULT 0,
                   is_filterable INTEGER DEFAULT 0,
                   FOREIGN KEY (category_id) REFERENCES categories(id)
               )
           ''')


           # 创建商品属性值表（attribute_value）
           # 表结构说明：
           #   id - 主键，自增长整数
           #   attribute_id - 关联属性表的外键，非空
           #   value - 属性值文本，非空
           #   image_url - 可选图片链接字段
           #   sort_order - 排序序号，默认值为0
           # 外键约束：attribute_id字段关联attribute表的id字段

           cursor.execute('''
               CREATE TABLE IF NOT EXISTS attribute_value (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   attribute_id INTEGER NOT NULL,
                   value TEXT NOT NULL,
                   image_url TEXT,
                   sort_order INTEGER DEFAULT 0,
                   FOREIGN KEY (attribute_id) REFERENCES attribute(id)
               )
           ''')



           # SPU-属性关联表
           #
           #创建SPU属性关联表，用于存储商品属性与SPU的关联关系
           #    表结构说明：
           #      - spu_id: 关联的SPU ID，外键引用spu表的id
           #       attribute_id: 属性ID，外键引用attribute表的id
           #      - value: 属性值文本内容
           #      - value_ids: 预定义属性值ID列表（JSON格式存储）
           #       - is_custom: 是否为自定义属性（0-预定义属性 1-自定义属性）
           #  外键约束确保数据完整性：
           #    - spU_id必须存在于spu表
           #   - attribute_id必须存在于attribute表
           #


           cursor.execute('''
               CREATE TABLE IF NOT EXISTS spu_attribute_value (
                   spu_id INTEGER NOT NULL,
                   attribute_id INTEGER NOT NULL,
                   value TEXT,
                   value_ids TEXT,
                   is_custom INTEGER DEFAULT 0,
                   FOREIGN KEY (spu_id) REFERENCES spu(id),
                   FOREIGN KEY (attribute_id) REFERENCES attribute(id)
               )
           ''')

           # 轮播图片表
           cursor.execute('''
                      CREATE TABLE IF NOT EXISTS carousel (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          image_url TEXT NOT NULL,
                          title TEXT,
                          description TEXT
                      )
                  ''')

           # 插入模拟数据到carousel表
           cursor.execute('''
                      SELECT COUNT(*) FROM carousel
                  ''')
           count = cursor.fetchone()[0]
           if count == 0:
               cursor.execute('''
                          INSERT INTO carousel (image_url, title, description) VALUES
                          ('static/images/carousel/lunbotu_1.jpg', '灵感穿搭', '灵感穿搭1折起'),
                          ('static/images/carousel/carsoul_2.jpg', '神仙水', '神仙水买230ml至高享390ml'),
                          ('static/images/carousel/carousol_3.jpg', '3·8换新节', '3·8换新节')
                      ''')

           conn.commit()




@app.before_request
def create_tables():
    init_db()



@app.route("/get_verification_code", methods=["GET"])
def get_verification_code():
    code = generate_verification_code()
    session['verification_code'] = code
    session['verification_code_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'verification_code': code}), 200



@app.route('/api/carousel', methods=['GET'])
def get_carousel():
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 查询所有有效的轮播图数据，按id升序排列
            cursor.execute('''
                   SELECT id, image_url, title, description 
                   FROM carousel 
                   ORDER BY id ASC
               ''')
            carousel_data = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "code": 200,
                "data": carousel_data,
                "message": "Success"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库查询失败: {str(e)}")
        return jsonify({
            "code": 500,
            "data": None,
            "message": "数据库操作失败"
        }), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({
            "code": 500,
            "data": None,
            "message": "服务器内部错误"
        }), 500







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



























