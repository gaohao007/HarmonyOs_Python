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

           # 商品分类表
           # #自增主键id、
           # 分类名称name、
           # 图片路径image、
           # 父分类id（默认0实现层级结构）和排序序号（默认0控制显示顺序）
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

           # 插入示例SPU数据
           cursor.execute('''
                      SELECT COUNT(*) FROM spu
                  ''')
           count = cursor.fetchone()[0]
           if count == 0:
               cursor.execute('''
                          INSERT INTO spu (name, description, category_id, main_image, detail_images) VALUES
                          ('GXG', '春季热卖GXG男装黑色连帽户外夹克男机能运动夹克休闲外套', 1, 'static/images/nanzhuang/man_1_1.jpg', '["static/images/nanzhuang/man_1_1.jpg", "static/images/nanzhuang/man_1_2.jpg","static/images/nanzhuang/man_1_3.jpg","static/images/nanzhuang/man_1_4.jpg","static/images/nanzhuang/man_1_5.jpg","static/images/nanzhuang/man_1_6.jpg"]'),
                          ('Reshake', '潮牌衬衫男士春夏长袖男装舒适百搭休闲痞帅宽松青少年男装衬衣男', 1, 'static/images/nanzhuang/man_2_1.jpg', '["static/images/nanzhuang/man_2_1.jpg", "static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]'),
                          ('马克华菲', '【后背时尚印花】春秋休闲工装翻领外套字母棒球男士复古夹克', 1, 'static/images/nanzhuang/man_3_1.jpg', '["static/images/nanzhuang/man_3_1.jpg", "static/images/nanzhuang/man_3_2.jpg","static/images/nanzhuang/man_3_3.jpg","static/images/nanzhuang/man_3_4.jpg","static/images/nanzhuang/man_3_5.jpg","static/images/nanzhuang/man_3_6.jpg"]'),
                          ('七匹狼', '春季时尚休闲舒适亲肤经典狼标刺绣男式卫衣', 1, 'static/images/nanzhuang/man_4_1.jpg', '["static/images/nanzhuang/man_4_1.jpg", "static/images/nanzhuang/man_4_2.jpg","static/images/nanzhuang/man_4_3.jpg","static/images/nanzhuang/man_4_4.jpg","static/images/nanzhuang/man_4_5.jpg","static/images/nanzhuang/man_4_6.jpg","static/images/nanzhuang/man_4_7.jpg","static/images/nanzhuang/man_4_8.jpg"]'),
                          ('URBAN REVIVO', 'UR秋季复古缝线条纹多口袋牛仔外套UML830009', 1, 'static/images/nanzhuang/man_5_1.jpg', '["static/images/nanzhuang/man_5_1.jpg", "static/images/nanzhuang/man_5_2.jpg","static/images/nanzhuang/man_5_3.jpg","static/images/nanzhuang/man_5_4.jpg"]'),
                          ('梦特娇', '【棉混纺&亲肤舒适】春季男士针织衫亲肤打底衫MTG', 1, 'static/images/nanzhuang/man_6_1.jpg', '["static/images/nanzhuang/man_6_1.jpg", "static/images/nanzhuang/man_6_2.jpg","static/images/nanzhuang/man_6_3.jpg","static/images/nanzhuang/man_6_4.jpg","static/images/nanzhuang/man_6_5.jpg","static/images/nanzhuang/man_6_6.jpg","static/images/nanzhuang/man_6_7.jpg","static/images/nanzhuang/man_6_8.jpg","static/images/nanzhuang/man_6_9.jpg","static/images/nanzhuang/man_6_10.jpg"]'),
                          ('梦特娇', '【立体华夫格&棉柔舒适】25春男式半高领针织提花开衫百搭外套', 1, 'static/images/nanzhuang/man_7_1.jpg', '["static/images/nanzhuang/man_7_1.jpg", "static/images/nanzhuang/man_7_2.jpg","static/images/nanzhuang/man_7_3.jpg","static/images/nanzhuang/man_7_4.jpg","static/images/nanzhuang/man_7_5.jpg","static/images/nanzhuang/man_7_6.jpg","static/images/nanzhuang/man_7_7.jpg","static/images/nanzhuang/man_7_8.jpg","static/images/nanzhuang/man_7_9.jpg","static/images/nanzhuang/man_7_10.jpg","static/images/nanzhuang/man_7_11.jpg","static/images/nanzhuang/man_7_12.jpg"]')
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

           # 插入示例SKU数据
           cursor.execute('''
                      SELECT COUNT(*) FROM sku
                  ''')
           count = cursor.fetchone()[0]
           if count == 0:
               cursor.execute('''
                          INSERT INTO sku (spu_id, price, stock, combination, image, status) VALUES
                          (1, 290.00, 40, 'Color:"黑色",Size:"S"', 'static/images/nanzhuang/man_1_1.jpg', 1),
                          (1, 290.00, 30, 'Color:"黑色",Size:"M"', 'static/images/nanzhuang/man_1_1.jpg', 1),
                          (1, 290.00, 40, 'Color:"黑色",Size:"L"', 'static/images/nanzhuang/man_1_1.jpg', 1),
                          (1, 290.00, 30, 'Color:"黑色",Size:"XL"', 'static/images/nanzhuang/man_1_1.jpg', 1),
                          (1, 290.00, 20, 'Color:"黑色",Size:"XXL"', 'static/images/nanzhuang/man_1_1.jpg', 1),
                          
                          (2, 75.00, 20, 'Color:"黑色",Size:"M"', 'static/images/nanzhuang/man_2_1.jpg', 1),
                          (2, 75.00, 40, 'Color:"黑色",Size:"L"', 'static/images/nanzhuang/man_2_1.jpg', 1),
                          (2, 75.00, 60, 'Color:"黑色",Size:"XL"', 'static/images/nanzhuang/man_2_1.jpg', 1),
                          (2, 75.00, 80, 'Color:"黑色",Size:"2XL"', 'static/images/nanzhuang/man_2_1.jpg', 1),
                          (2, 75.00, 30, 'Color:"黑色",Size:"3XL"', 'static/images/nanzhuang/man_2_1.jpg', 1),
                          (2, 75.00, 13, 'Color:"黑色",Size:"4XL"', 'static/images/nanzhuang/man_2_1.jpg', 1),
                          
                          (3, 179.00, 19, 'Color:"黑色",Size:"S"', 'static/images/nanzhuang/man_3_1.jpg', 1),
                          (3, 179.00, 32, 'Color:"黑色",Size:"M"', 'static/images/nanzhuang/man_3_1.jpg', 1),
                          (3, 179.00, 45, 'Color:"黑色",Size:"L"', 'static/images/nanzhuang/man_3_1.jpg', 1),
                          (3, 179.00, 56, 'Color:"黑色",Size:"XL"', 'static/images/nanzhuang/man_3_1.jpg', 1),
                          (3, 179.00, 68, 'Color:"黑色",Size:"2XL"', 'static/images/nanzhuang/man_3_1.jpg', 1),
                          (3, 179.00, 25, 'Color:"黑色",Size:"3XL"', 'static/images/nanzhuang/man_3_1.jpg', 1),
                          
                          (4, 107.00, 21, 'Color:"黑色",Size:"48"', 'static/images/nanzhuang/man_4_1.jpg', 1),
                          (4, 107.00, 12, 'Color:"黑色",Size:"50"', 'static/images/nanzhuang/man_4_1.jpg', 1),
                          (4, 107.00, 12, 'Color:"黑色",Size:"52"', 'static/images/nanzhuang/man_4_1.jpg', 1),
                          (4, 107.00, 4, 'Color:"黑色",Size:"54"', 'static/images/nanzhuang/man_4_1.jpg', 1),
                          
                
                          (5, 132.00, 10, 'Color:"黑灰色条纹",Size:"L"', 'static/images/nanzhuang/man_5_1.jpg', 1),
                          
                          (6, 123.00, 1, 'Color:"中灰",Size:"54"', 'static/images/nanzhuang/man_6_1.jpg', 1),                  
                          (6, 123.00, 2, 'Color:"黑灰",Size:"50"', 'static/images/nanzhuang/m5_5_2_1.jpg', 1),
                          (6, 123.00, 3, 'Color:"黑灰",Size:"48"', 'static/images/nanzhuang/m5_5_2_1.jpg', 1),
                          (6, 123.00, 3, 'Color:"黑灰",Size:"52"', 'static/images/nanzhuang/m5_5_2_1.jpg', 1),
                          (6, 123.00, 2, 'Color:"黑灰",Size:"54"', 'static/images/nanzhuang/m5_5_2_1.jpg', 1),
                          
                          (7, 371.00, 8, 'Color:"藏青",Size:"48"', 'static/images/nanzhuang/man_7_1.jpg', 1),
                          (7, 371.00, 8, 'Color:"藏青",Size:"50"', 'static/images/nanzhuang/man_7_1.jpg', 1),
                          (7, 371.00, 8, 'Color:"藏青",Size:"52"', 'static/images/nanzhuang/man_7_1.jpg', 1),
                          (7, 371.00, 8, 'Color:"藏青",Size:"54"', 'static/images/nanzhuang/man_7_1.jpg', 1);
      
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

@app.route('/api/products', methods=['GET'])
def get_products():
    """
    获取商品列表接口
    返回格式：
    {
        "code": 状态码,
        "data": [
            {
                "id": 商品ID,
                "name": 商品名称,
                "description": 商品描述,
                "category_id": 分类ID,
                "main_image": 主图存储路径,
                "detail_images": 详情图路径列表,
                "created_at": 创建时间,
                "skus": [
                    {
                        "id": SKU ID,
                        "price": 价格,
                        "stock": 库存数量,
                        "combination": 规格组合,
                        "image": 商品展示图路径,
                        "status": 商品状态
                    }
                ],
                "attributes": [
                    {
                        "attribute_id": 属性ID,
                        "attribute_name": 属性名称,
                        "value": 属性值
                    }
                ]
            }
        ],
        "message": 状态描述
    }
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 查询所有SPU数据
            cursor.execute('''
                SELECT id, name, description, category_id, main_image, detail_images, created_at 
                FROM spu
            ''')
            spu_data = [dict(row) for row in cursor.fetchall()]

            # 查询所有SKU数据
            cursor.execute('''
                SELECT id, spu_id, price, stock, combination, image, status 
                FROM sku
            ''')
            sku_data = [dict(row) for row in cursor.fetchall()]

            # 查询所有SPU-属性关联数据
            cursor.execute('''
                SELECT sav.spu_id, sav.attribute_id, av.value, a.name AS attribute_name
                FROM spu_attribute_value sav
                JOIN attribute_value av ON sav.value_ids LIKE '%' || av.id || '%'
                JOIN attribute a ON sav.attribute_id = a.id
            ''')
            attribute_data = [dict(row) for row in cursor.fetchall()]

            # 构建商品列表
            products = []
            for spu in spu_data:
                product = {
                    "id": spu['id'],
                    "name": spu['name'],
                    "description": spu['description'],
                    "category_id": spu['category_id'],
                    "main_image": spu['main_image'],
                    "detail_images": spu['detail_images'],
                    "created_at": spu['created_at'],
                    "skus": [],
                    "attributes": []
                }

                # 添加SKU信息
                product['skus'] = [
                    {
                        "id": sku['id'],
                        "price": sku['price'],
                        "stock": sku['stock'],
                        "combination": sku['combination'],
                        "image": sku['image'],
                        "status": sku['status']
                    }
                    for sku in sku_data if sku['spu_id'] == spu['id']
                ]

                # 添加属性信息
                product['attributes'] = [
                    {
                        "attribute_id": attr['attribute_id'],
                        "attribute_name": attr['attribute_name'],
                        "value": attr['value']
                    }
                    for attr in attribute_data if attr['spu_id'] == spu['id']
                ]

                products.append(product)

            return jsonify({
                "code": 200,
                "data": products,
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



























