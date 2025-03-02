import json

from flask import Flask, session,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from flask_jwt_extended  import  JWTManager,create_access_token,jwt_required,get_jwt_identity
from datetime import timedelta,datetime
import random
import  string
from base import *


app = Flask(__name__)

# 配置JWT 秘钥
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
# 初始化JWT�化JWT = JWTManager()
jwt = JWTManager(app)

# 设置session密钥
app.secret_key = 'your-code-key'


def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))


# 配置数据库
import sqlite3

DATABASE = 'database.db'


def init_db():
    # 链接数据库db = SQLite3
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # 地理位置表
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS locations (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   parent_id INTEGER DEFAULT 0,
                   FOREIGN KEY (parent_id) REFERENCES locations(id)
               )
           ''')

        # 用户表优化
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT NOT NULL UNIQUE,
                   password TEXT NOT NULL,
                   email TEXT NOT NULL UNIQUE,
                   phone TEXT DEFAULT '13200984321',
                   avatar TEXT DEFAULT 'static/images/touxiang.png',
                   gender INTEGER DEFAULT 0 CHECK(gender IN (0,1,2)),
                   status INTEGER DEFAULT 1 CHECK(status IN (0,1)),
                   last_login DATETIME,  -- 新增最后登录时间
                   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                   updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                   is_deleted BOOLEAN DEFAULT 0  -- 新增软删除标记
               )
           ''')

        # 用户地址表优化
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS user_address (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   name TEXT NOT NULL,
                   phone TEXT NOT NULL,
                   province TEXT NOT NULL,
                   city TEXT NOT NULL,
                   district TEXT NOT NULL,
                   detail TEXT NOT NULL,
                   is_default BOOLEAN DEFAULT 0 CHECK(is_default IN (0,1)),
                   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
               )
           ''')
        # 商品模块
        cursor.execute('''
                  CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        parent_id INTEGER DEFAULT 0,
                        image TEXT,
                        sort_order INTEGER DEFAULT 0
                        )
              ''')
        # 插入模拟数据到categories表
        cursor.execute('''
                                SELECT COUNT(*) FROM categories
                            ''')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('''
                                    INSERT INTO categories ( name,image) VALUES
                                    ('男装','static/images/nanzhuang.jpg'),
                                    ('女装','static/images/nvzhuang.jpeg'),
                                    ('男鞋','static/images/nanxie.jpeg'),
                                    ('女鞋','static/images/nvxie.jpg'),
                                    ('童装','static/images/tongzhuang.jpg'),
                                    ('美妆','static/images/meizhuang.jpeg'),
                                    ('内衣','static/images/neiyi.jpg'),
                                    ('宠物','static/images/congwu.png');

                                ''')

        cursor.execute("""
           CREATE TABLE IF NOT EXISTS attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                input_type INTEGER DEFAULT 1,  -- 1-单选 2-多选
                is_required BOOLEAN DEFAULT 1);
           """)

        # 插入基础属性数据
        cursor.execute('''
                      SELECT COUNT(*) FROM attributes
                  ''')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                          INSERT INTO attributes (name, input_type) VALUES
                          ('颜色', 1),
                          ('尺码', 1),
                          ('面料', 1),
                          ('季节', 1),
                          ('规格',1),
                          ('单位',1)
                      ''')

        cursor.execute("""           
                    CREATE TABLE IF NOT EXISTS attribute_values (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        attribute_id INTEGER NOT NULL,
                        value TEXT NOT NULL,
                        FOREIGN KEY (attribute_id) REFERENCES attributes(id)
                    );
           """)
        # 插入基础属性数据
        cursor.execute('''
                      SELECT COUNT(*) FROM attribute_values
                  ''')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                     INSERT INTO attribute_values (attribute_id, value) VALUES
                            (1, '黑色') ,(1, '米杏'),(1, '蓝色'),(1, '米白'), (1, '白色'), (1, '咖啡'), (1, '藏青'), (1, '米色'),(1,'中灰'),(1,'黑灰色条纹'),(1,'深宝'),
                            (2, 'S'), (2, '均码'),(2, 'M'), (2, 'M(建议体重5~8斤)'), (2, 'S(建议体重3~5斤)'),(2, 'XS(建议体重1~3斤)'),(2, 'L'), (2, 'XL'), (2, 'XXL'), (2, 'XXXL'),(2, 'XXXXL'),(2, '35'),(2,'36'),(2,'37'),(2,'38'),(2,'39'),(2,'40'),(2,'48'),(2,'50'),(2,'52'),(2,'54'),(2,'58'),(2,'60'),
                            (3, '纯棉'), (3, '涤纶'), (3, '混纺'),
                            (4, '春季'), (4, '夏季'), (4, '秋季'), (4, '冬季'),
                            (5,'净含量'),(5,'规格'),
                            (6,'30ml'),(6,'100g')
                      ''')

        # 品牌表
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS brands (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL UNIQUE,
                   logo TEXT NOT NULL,
                   story TEXT,  -- 品牌故事
                   backimg TEXT,
                   sort_order INTEGER DEFAULT 0,
                   is_recommend BOOLEAN DEFAULT 1  -- 是否推荐品牌
               );
           ''')

        cursor.execute('''
                    SELECT COUNT(*) FROM brands
           ''')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('''
                             INSERT INTO brands ( name,logo,story,backimg) VALUES
                                    ('GXG','static/images/BrandLogo/GXG/logo.png','GXG通过聚焦都市通勤场景区隔于过于严肃的商务和过于随意的运动风格带来“上班穿，刚刚好”的品质服装旨在让都市中人享受得体、舒适、时尚的零压通勤生活。','static/images/BrandLogo/GXG/back.jpg'),
                                    ('Reshake','static/images/BrandLogo/Reshake/logo.png','RESHAKE是时装化街头潮牌，隶属于马克华菲集团旗下， 坚持以“KEEPITREAL-做你自己”为品牌核心， 通过简洁、张扬和富有节奏感的服装设计， 为热衷于街头文化的年轻人， 创造具有高街时尚感的全新潮牌。“上班穿，刚刚好”的品质服装旨在让都市中人享受得体、舒适、时尚的零压通勤生活。','static/images/BrandLogo/Reshake/back.jpg'),
                                    ('马克华菲','static/images/BrandLogo/马克华菲/logo.png','马克华菲创建于魅力时尚之都上海，是国际设计大师Mark Cheung为世界都市新贵度身定制的中国原创设计时尚品牌，自2001年诞生以来深得世界时尚人士青睐。摩登在造，越界型走是为其标语。','static/images/BrandLogo/马克华菲/back.jpg'),
                                    ('七匹狼','static/images/BrandLogo/七匹狼/logo.png','','static/images/BrandLogo/七匹狼/back.jpg'),
                                    ('URBAN REVIVO','static/images/BrandLogo/URBAN/logo.png','简称UR，以“玩味时尚”作为品牌理念，突破传统快时尚思维，打造“快奢时尚”的品牌定位。UR致力将有趣的、新鲜的、跨越领域的当代时尚新思维与消费者共同分享，让每个人都能创造属于自己的时尚风格。','static/images/BrandLogo/URBAN/back.jpg'),
                                    ('梦特娇','static/images/BrandLogo/梦特娇/logo.png','梦特娇MONTAGUT是于1880年成立的百年时尚品牌，品牌登陆中国发展30余年，拥有超过 3000 个销售点，梦特娇一直秉承“优雅、时尚、浪漫”的理念，以简洁新意的设计、考究的工艺、独特的风格韵味而深受消费者喜爱。','static/images/BrandLogo/梦特娇/back.jpg'),
                                    ('西町村屋','static/images/BrandLogo/西町村屋/logo.png','我始终害怕SETIR0M.西町村屋会成为毫无灵魂的符号我常把我们想做的想象成一只有重量的金色手镯戴在小麦肤色手腕上笑而不语、魅力迷人她饱读诗书、曾四处旅行深藏诸多有趣的见闻SETIROM.西町村屋新女性主义美学生活品牌','static/images/BrandLogo/西町村屋/back.jpg'),
                                    ('美丽衣橱','static/images/BrandLogo/美丽衣橱/logo.png','美丽衣橱，始于2011年。以原创设计为画笔，勾勒描墨中国女性时尚、自信、独立、阳光的形象。打破原创设计的边界，以匠心沉淀品质的温度，以作品讲诉年华的故事。美丽衣橱，女人的衣橱!','static/images/BrandLogo/美丽衣橱/back.jpg'),
                                    ('嬉皮狗','static/images/BrandLogo/嬉皮狗/logo.png','','static/images/BrandLogo/嬉皮狗/back.jpg'),
                                    ('ZHR则则','static/images/BrandLogo/ZHR则则/logo.png','ZHR是一家注重脚感和细节的有态度的品牌：品牌专注于女鞋，通过充满时尚感的设计、高舒适度的穿着体验、符合人体工学的设计原理，为顾客呈现高性价比的优质产品。','static/images/BrandLogo/ZHR则则/back.jpg'),
                                    ('unkown','static/images/BrandLogo/ZHR则则/logo.png','','');
                                ''')

        cursor.execute("""
               CREATE TABLE IF NOT EXISTS spu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    brand_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    main_image TEXT NOT NULL,
                    detail_images TEXT,  -- JSON array
                    sales_count INTEGER DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    status INTEGER DEFAULT 1,  -- 0-下架 1-上架
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_hot BOOLEAN DEFAULT 0,  -- 是否热销
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    FOREIGN KEY (brand_id) REFERENCES brands(id)
               );       
           """)

        # 插入SPU数据
        cursor.execute('''
                     SELECT COUNT(*) FROM spu
                 ''')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('''
                          INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                          (1, 1, 'GXG男装', '春季热卖GXG男装黑色连帽户外夹克男机能运动夹克休闲外套', 
                          'static/images/nanzhuang/man_1_1.jpg',
                          '["static/images/nanzhuang/man_1_1.jpg","static/images/nanzhuang/man_1_2.jpg","static/images/nanzhuang/man_1_3.jpg","static/images/nanzhuang/man_1_4.jpg","static/images/nanzhuang/man_1_5.jpg","static/images/nanzhuang/man_1_6.jpg"]', 1),

                          (1, 2, '男士春夏长袖男装', '潮牌衬衫男士春夏长袖男装舒适百搭休闲痞帅宽松青少年男装衬衣男', 
                          'static/images/nanzhuang/man_2_1.jpg',
                          '["static/images/nanzhuang/man_2_1.jpg","static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]', 0),

                          (1, 4, '刺绣男式卫衣', '春季时尚休闲舒适亲肤经典狼标刺绣男式卫衣', 
                          'static/images/nanzhuang/man_4_1.jpg',
                          '["static/images/nanzhuang/man_4_1.jpg","static/images/nanzhuang/man_4_2.jpg","static/images/nanzhuang/man_4_3.jpg","static/images/nanzhuang/man_4_4.jpg","static/images/nanzhuang/man_4_5.jpg","static/images/nanzhuang/man_4_6.jpg","static/images/nanzhuang/man_4_7.jpg","static/images/nanzhuang/man_4_8.jpg"]', 0),
                          
                          
                          (1, 3, '男士复古夹克', '【后背时尚印花】春秋休闲工装翻领外套字母棒球男士复古夹克', 
                          'static/images/nanzhuang/man_3_1.jpg',
                          '["static/images/nanzhuang/man_3_1.jpg","static/images/nanzhuang/man_3_2.jpg","static/images/nanzhuang/man_3_3.jpg","static/images/nanzhuang/man_3_4.jpg","static/images/nanzhuang/man_3_5.jpg","static/images/nanzhuang/man_3_6.jpg"]', 1)

                      ''')
            cursor.execute("""
                    INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                        (1, 5, 'UR秋季复古缝线条纹多口袋牛仔外套', 'UR秋季复古缝线条纹多口袋牛仔外套UML830009', 
                          'static/images/nanzhuang/man_5_1.jpg',
                          '["static/images/nanzhuang/man_5_1.jpg","static/images/nanzhuang/man_5_2.jpg","static/images/nanzhuang/man_5_3.jpg","static/images/nanzhuang/man_5_4.jpg"]', 0
                        )
            """)

            cursor.execute("""
                                INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                                    (1, 6, '春季男士针织衫亲肤打底衫', '【棉混纺&亲肤舒适】春季男士针织衫亲肤打底衫MTG', 
                                      'static/images/nanzhuang/man_6_1.jpg',
                                      '["static/images/nanzhuang/man_6_1.jpg","static/images/nanzhuang/man_6_2.jpg","static/images/nanzhuang/man_6_3.jpg","static/images/nanzhuang/man_6_4.jpg","static/images/nanzhuang/man_6_5.jpg","static/images/nanzhuang/man_6_6.jpg","static/images/nanzhuang/man_6_7.jpg","static/images/nanzhuang/man_6_8.jpg","static/images/nanzhuang/man_6_9.jpg","static/images/nanzhuang/man_6_10.jpg"]', 0
                                    )
                        """)

            cursor.execute("""
                       INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                       (1, 6, '25春男式半高领针织提花开衫百搭外套', '【立体华夫格&棉柔舒适】25春男式半高领针织提花开衫百搭外套', 
                             'static/images/nanzhuang/man_7_1.jpg',
                             '["static/images/nanzhuang/man_7_1.jpg","static/images/nanzhuang/man_7_2.jpg","static/images/nanzhuang/man_7_3.jpg","static/images/nanzhuang/man_7_4.jpg"]', 0
                       )
            """)

            #女装
            cursor.execute("""
                   INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                        (2, 7, '女士冬季长袖衬衫', '女士冬季长袖衬衫撞色刺绣木耳边衬衫', 
                            'static/images/nvzhuang/f_1_1.jpg',
                            '["static/images/nvzhuang/f_1_1.jpg","static/images/nvzhuang/f_1_2.jpg","static/images/nvzhuang/f_1_3.jpg","static/images/nvzhuang/f_1_4.jpg"]',1
                        )
            """)

            cursor.execute("""
               INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                       (2, 7, '连衣裙女', '连衣裙女春秋法式收腰V领高级感春季连衣裙商场同款', 
                               'static/images/nvzhuang/f_2_1.jpg',
                      '["static/images/nvzhuang/f_2_1.jpg","static/images/nvzhuang/f_2_2.jpg","static/images/nvzhuang/f_2_3.jpg","static/images/nvzhuang/f_2_4.jpg"]',0
               )
            """)

            cursor.execute("""
                          INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                                  (2, 5, 'UR2024夏季女装', 'UR2024夏季女装都市通勤气质风超宽松西装外套UWU140026', 
                                          'static/images/nvzhuang/f_3_1.jpg',
                                 '["static/images/nvzhuang/f_3_1.jpg","static/images/nvzhuang/f_3_2.jpg","static/images/nvzhuang/f_3_3.jpg","static/images/nvzhuang/f_3_4.jpg"]',0
                          )
            """)

            cursor.execute("""
                  INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                    (2,11, '浮雕提花公主裙两件套春季连衣短裙', '浮雕提花公主裙两件套春季连衣短裙', 
                    'static/images/nvzhuang/f_4_1.jpg',
                    '["static/images/nvzhuang/f_4_1.jpg","static/images/nvzhuang/f_4_2.jpg","static/images/nvzhuang/f_4_3.jpg","static/images/nvzhuang/f_4_4.jpg"]',1
                  )
            """)

            #美妆
            cursor.execute("""
                INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                    (6,11, '净透控油清洁泥膜', '【改善黑头】净透控油清洁泥膜100g清爽保湿深层清洁毛孔', 
                    'static/images/meizhuang/m1_1.jpg',
                    '["static/images/meizhuang/m1_1.jpg","static/images/meizhuang/m1_2.jpg","static/images/meizhuang/m1_3.jpg","static/images/meizhuang/m1_4.jpg"]',1
                )
            """)

            cursor.execute("""
                INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                    (6,11, '虾青素精华液面部精华补水甘油保湿烟酰胺提亮肤色小棕瓶60ml', '虾青素精华液面部精华补水甘油保湿烟酰胺提亮肤色小棕瓶60ml', 
                    'static/images/meizhuang/m2_1.jpg',
                    '["static/images/meizhuang/m2_1.jpg","static/images/meizhuang/m2_2.jpg","static/images/meizhuang/m2_3.jpg","static/images/meizhuang/m2_4.jpg"]',0
                )
            """)
            #童装
            cursor.execute("""
                INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                    (5,11, '【100%云感棉】男士保暖内衣套装青少年秋衣秋裤大童打底衣', '【100%云感棉】男士保暖内衣套装青少年秋衣秋裤大童打底衣', 
                    'static/images/tongzhuang/t1_1.jpg',
                    '["static/images/tongzhuang/t1_1.jpg","static/images/tongzhuang/t1_2.jpg","static/images/tongzhuang/t1_3.jpg","static/images/tongzhuang/t1_4.jpg"]',0
                )
            """)
            #男鞋
            cursor.execute("""
                INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                    (3,11, '【头层牛皮】2025春季男士新款休闲鞋子百搭复古德训鞋男板鞋', '【头层牛皮】2025春季男士新款休闲鞋子百搭复古德训鞋男板鞋', 
                    'static/images/nanxie/nx1_1.jpg',
                    '["static/images/nanxie/nx1_1.jpg","static/images/nanxie/nx1_2.jpg","static/images/nanxie/nx1_3.jpg","static/images/nanxie/nx1_4.jpg"]',1
                )
            """)

            #女鞋
            cursor.execute("""
                 INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                    (4,10, '【增高厚底】春季板鞋女2025百搭简约舒适小白鞋运动女休闲鞋', '【增高厚底】春季板鞋女2025百搭简约舒适小白鞋运动女休闲鞋', 
                    'static/images/nvxie/nx1_1.jpg',
                    '["static/images/nvxie/nx1_1.jpg","static/images/nvxie/nx1_2.jpg","static/images/nvxie/nx1_3.jpg","static/images/nvxie/nx1_4.jpg"]',1
                )
            """)
            #内衣

            cursor.execute("""
                INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                    (7,11, '【增高厚底】春季板鞋女2025百搭简约舒适小白鞋运动女休闲鞋', '【云朵绵可爱小兔子】秋冬女士睡衣甜美长袖长裤可外穿家居服套装', 
                    'static/images/neiyi/n2_1.jpg',
                    '["static/images/neiyi/n2_1.jpg","static/images/neiyi/n2_2.jpg","static/images/neiyi/n2_3.jpg","static/images/neiyi/n2_4.jpg"]',1
                )
            """)

            #宠物
            cursor.execute("""
            INSERT INTO spu (category_id, brand_id, name, description, main_image, detail_images, is_hot) VALUES
                    (8,9, '小猫咪衣服防掉毛多彩毛球毛衣布偶幼猫薄款蓝猫渐层宠物狗狗秋冬', '小猫咪衣服防掉毛多彩毛球毛衣布偶幼猫薄款蓝猫渐层宠物狗狗秋冬', 
                    'static/images/congwu/w_1_1.jpg',
                    '["static/images/congwu/w_1_1.jpg","static/images/congwu/w_1_2.jpg","static/images/congwu/w_1_3.jpg","static/images/congwu/w_1_4.jpg"]',1
                )
            """)






        cursor.execute("""          
                    CREATE TABLE IF NOT EXISTS sku (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        spu_id INTEGER NOT NULL,
                        price DECIMAL(10,2) NOT NULL,
                        stock INTEGER NOT NULL CHECK(stock >= 0),
                        attributes JSON NOT NULL,  -- 格式：[{"attribute_id":1, "value":"红色"}]
                        image TEXT,
                        status INTEGER DEFAULT 1,  -- 0-下架 1-上架
                        version INTEGER DEFAULT 1,  -- 乐观锁
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (spu_id) REFERENCES spu(id)
                    );
           """)
        # 插入SKU数据
        cursor.execute('''
                      SELECT COUNT(*) FROM sku
                  ''')
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("""

                           INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                           -- 西装外套SKU
                           (1, 290.00, 33, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"S"}]',
                           '["static/images/nanzhuang/man_1_1.jpg","static/images/nanzhuang/man_1_2.jpg","static/images/nanzhuang/man_1_3.jpg","static/images/nanzhuang/man_1_4.jpg","static/images/nanzhuang/man_1_5.jpg","static/images/nanzhuang/man_1_6.jpg"]'),

                           (1, 290.00, 28, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"M"}]',
                           '["static/images/nanzhuang/man_1_1.jpg","static/images/nanzhuang/man_1_2.jpg","static/images/nanzhuang/man_1_3.jpg","static/images/nanzhuang/man_1_4.jpg","static/images/nanzhuang/man_1_5.jpg","static/images/nanzhuang/man_1_6.jpg"]'),


                           (1, 290.00, 23, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"L"}]',
                           '["static/images/nanzhuang/man_1_1.jpg","static/images/nanzhuang/man_1_2.jpg","static/images/nanzhuang/man_1_3.jpg","static/images/nanzhuang/man_1_4.jpg","static/images/nanzhuang/man_1_5.jpg","static/images/nanzhuang/man_1_6.jpg"]'),

                           (1, 290.00, 45, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XL"}]',
                           '["static/images/nanzhuang/man_1_1.jpg","static/images/nanzhuang/man_1_2.jpg","static/images/nanzhuang/man_1_3.jpg","static/images/nanzhuang/man_1_4.jpg","static/images/nanzhuang/man_1_5.jpg","static/images/nanzhuang/man_1_6.jpg"]'),


                           (1, 290.00, 12, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XXL"}]',
                           '["static/images/nanzhuang/man_1_1.jpg","static/images/nanzhuang/man_1_2.jpg","static/images/nanzhuang/man_1_3.jpg","static/images/nanzhuang/man_1_4.jpg","static/images/nanzhuang/man_1_5.jpg","static/images/nanzhuang/man_1_6.jpg"]'),

                           (1, 290.00, 34, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XXXL"}]',
                           '["static/images/nanzhuang/man_1_1.jpg","static/images/nanzhuang/man_1_2.jpg","static/images/nanzhuang/man_1_3.jpg","static/images/nanzhuang/man_1_4.jpg","static/images/nanzhuang/man_1_5.jpg","static/images/nanzhuang/man_1_6.jpg"]'),

                           -- 男士春夏长袖男装
                           (2, 75.00, 20, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"M"}]',
                           '["static/images/nanzhuang/man_2_1.jpg","static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]'),

                           (2, 75.00, 40, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"L"}]',
                           '["static/images/nanzhuang/man_2_1.jpg","static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]'),

                           (2, 75.00, 38, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XL"}]',
                           '["static/images/nanzhuang/man_2_1.jpg","static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]'),

                           (2, 75.00, 34, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XXL"}]',
                           '["static/images/nanzhuang/man_2_1.jpg","static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]'),

                            (2, 75.00, 45, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XXXL"}]',
                           '["static/images/nanzhuang/man_2_1.jpg","static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]'),

                           (2, 75.00, 12, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XXXXL"}]',
                           '["static/images/nanzhuang/man_2_1.jpg","static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]'),


                           --中灰

                            (2, 75.00, 13, 
                           '[{"attribute_id":1, "value":"中灰"}, {"attribute_id":2, "value":"M"}]',
                           '["static/images/nanzhuang/man_2_2_1.jpg","static/images/nanzhuang/man_2_2_2.jpg","static/images/nanzhuang/man_2_2_3.jpg","static/images/nanzhuang/man_2_2_4.jpg","static/images/nanzhuang/man_2_2_5.jpg"]'),

                           (2, 75.00, 34, 
                           '[{"attribute_id":1, "value":"中灰"}, {"attribute_id":2, "value":"L"}]',
                           '["static/images/nanzhuang/man_2_2_1.jpg","static/images/nanzhuang/man_2_2_2.jpg","static/images/nanzhuang/man_2_2_3.jpg","static/images/nanzhuang/man_2_2_4.jpg","static/images/nanzhuang/man_2_2_5.jpg"]'),

                           (2, 75.00, 36, 
                           '[{"attribute_id":1, "value":"中灰"}, {"attribute_id":2, "value":"XL"}]',
                           '["static/images/nanzhuang/man_2_2_1.jpg","static/images/nanzhuang/man_2_2_2.jpg","static/images/nanzhuang/man_2_2_3.jpg","static/images/nanzhuang/man_2_2_4.jpg","static/images/nanzhuang/man_2_2_5.jpg"]'),

                           (2, 75.00, 32, 
                           '[{"attribute_id":1, "value":"中灰"}, {"attribute_id":2, "value":"XXL"}]',
                           '["static/images/nanzhuang/man_2_2_1.jpg","static/images/nanzhuang/man_2_2_2.jpg","static/images/nanzhuang/man_2_2_3.jpg","static/images/nanzhuang/man_2_2_4.jpg","static/images/nanzhuang/man_2_2_5.jpg"]'),

                            (2, 75.00, 18, 
                           '[{"attribute_id":1, "value":"中灰"}, {"attribute_id":2, "value":"XXXL"}]',
                           '["static/images/nanzhuang/man_2_2_1.jpg","static/images/nanzhuang/man_2_2_2.jpg","static/images/nanzhuang/man_2_2_3.jpg","static/images/nanzhuang/man_2_2_4.jpg","static/images/nanzhuang/man_2_2_5.jpg"]'),

                           (2, 75.00, 9, 
                           '[{"attribute_id":1, "value":"中灰"}, {"attribute_id":2, "value":"XXXXL"}]',
                           '["static/images/nanzhuang/man_2_2_1.jpg","static/images/nanzhuang/man_2_2_2.jpg","static/images/nanzhuang/man_2_2_3.jpg","static/images/nanzhuang/man_2_2_4.jpg","static/images/nanzhuang/man_2_2_5.jpg"]'),


                               --白色

                            (2, 75.00, 11, 
                           '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"M"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),

                           (2, 75.00, 23, 
                           '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"L"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),

                           (2, 75.00, 21, 
                           '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"XL"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),

                           (2, 75.00, 17, 
                           '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"XXL"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),
                            (2, 75.00, 6, 
                           '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"XXXL"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),
                           (2, 75.00, 3, 
                           '[{"attribute_id":1, "value":"中灰"}, {"attribute_id":2, "value":"XXXXL"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]')                           
            """)
            #七匹狼
            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                    (3, 107.00, 3, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"52"}]',
                        '["static/images/nanzhuang/man_4_1.jpg","static/images/nanzhuang/man_4_2.jpg","static/images/nanzhuang/man_4_3.jpg","static/images/nanzhuang/man_4_4.jpg","static/images/nanzhuang/man_4_5.jpg","static/images/nanzhuang/man_4_6.jpg","static/images/nanzhuang/man_4_7.jpg","static/images/nanzhuang/man_4_8.jpg"]'
                    ),
                    
                    (3, 107.00, 6, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"54"}]',
                        '["static/images/nanzhuang/man_4_1.jpg","static/images/nanzhuang/man_4_2.jpg","static/images/nanzhuang/man_4_3.jpg","static/images/nanzhuang/man_4_4.jpg","static/images/nanzhuang/man_4_5.jpg","static/images/nanzhuang/man_4_6.jpg","static/images/nanzhuang/man_4_7.jpg","static/images/nanzhuang/man_4_8.jpg"]'
                    ),
                    
                    (3, 107.00, 0, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"56"}]',
                        '["static/images/nanzhuang/man_4_1.jpg","static/images/nanzhuang/man_4_2.jpg","static/images/nanzhuang/man_4_3.jpg","static/images/nanzhuang/man_4_4.jpg","static/images/nanzhuang/man_4_5.jpg","static/images/nanzhuang/man_4_6.jpg","static/images/nanzhuang/man_4_7.jpg","static/images/nanzhuang/man_4_8.jpg"]'
                    ),
                    
                    (3, 107.00, 3, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"60"}]',
                        '["static/images/nanzhuang/man_4_1.jpg","static/images/nanzhuang/man_4_2.jpg","static/images/nanzhuang/man_4_3.jpg","static/images/nanzhuang/man_4_4.jpg","static/images/nanzhuang/man_4_5.jpg","static/images/nanzhuang/man_4_6.jpg","static/images/nanzhuang/man_4_7.jpg","static/images/nanzhuang/man_4_8.jpg"]'
                    )
                        
                       
            """)
            #男士复古夹克
            cursor.execute("""
                    INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                        (4, 179.00, 12, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"S"}]',
                        '["static/images/nanzhuang/man_3_1.jpg","static/images/nanzhuang/man_3_2.jpg","static/images/nanzhuang/man_3_3.jpg","static/images/nanzhuang/man_3_4.jpg","static/images/nanzhuang/man_3_5.jpg","static/images/nanzhuang/man_3_6.jpg"]'
                        ),
                        (4, 179.00, 18, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"M"}]',
                        '["static/images/nanzhuang/man_3_1.jpg","static/images/nanzhuang/man_3_2.jpg","static/images/nanzhuang/man_3_3.jpg","static/images/nanzhuang/man_3_4.jpg","static/images/nanzhuang/man_3_5.jpg","static/images/nanzhuang/man_3_6.jpg"]'
                        ),
                        (4, 179.00, 34, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"L"}]',
                        '["static/images/nanzhuang/man_3_1.jpg","static/images/nanzhuang/man_3_2.jpg","static/images/nanzhuang/man_3_3.jpg","static/images/nanzhuang/man_3_4.jpg","static/images/nanzhuang/man_3_5.jpg","static/images/nanzhuang/man_3_6.jpg"]'
                        ),
                        (4, 179.00, 23, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XL"}]',
                        '["static/images/nanzhuang/man_3_1.jpg","static/images/nanzhuang/man_3_2.jpg","static/images/nanzhuang/man_3_3.jpg","static/images/nanzhuang/man_3_4.jpg","static/images/nanzhuang/man_3_5.jpg","static/images/nanzhuang/man_3_6.jpg"]'
                        ),
                        (4, 179.00, 19, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XXL"}]',
                        '["static/images/nanzhuang/man_3_1.jpg","static/images/nanzhuang/man_3_2.jpg","static/images/nanzhuang/man_3_3.jpg","static/images/nanzhuang/man_3_4.jpg","static/images/nanzhuang/man_3_5.jpg","static/images/nanzhuang/man_3_6.jpg"]'
                        ),
                        (4, 179.00, 8, 
                       '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"XXL"}]',
                        '["static/images/nanzhuang/man_3_1.jpg","static/images/nanzhuang/man_3_2.jpg","static/images/nanzhuang/man_3_3.jpg","static/images/nanzhuang/man_3_4.jpg","static/images/nanzhuang/man_3_5.jpg","static/images/nanzhuang/man_3_6.jpg"]'
                        )
            """)
            #UR秋季复古缝线条纹多口袋牛仔外套
            cursor.execute("""
                                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                                    (5, 132.00, 8, 
                                   '[{"attribute_id":1, "value":"黑灰色条纹"}, {"attribute_id":2, "value":"L"}]',
                                    '["static/images/nanzhuang/man_5_1.jpg","static/images/nanzhuang/man_5_2.jpg","static/images/nanzhuang/man_5_3.jpg","static/images/nanzhuang/man_5_4.jpg"]'
                                    )
                                   
                        """)
            #春季男士针织衫亲肤打底衫
            cursor.execute("""
                      INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                             (6, 123.00, 1, 
                              '[{"attribute_id":1, "value":"中灰"}, {"attribute_id":2, "value":"54"}]',
                               '["static/images/nanzhuang/man_6_1.jpg","static/images/nanzhuang/man_6_2.jpg","static/images/nanzhuang/man_6_3.jpg","static/images/nanzhuang/man_6_4.jpg","static/images/nanzhuang/man_6_5.jpg","static/images/nanzhuang/man_6_6.jpg","static/images/nanzhuang/man_6_7.jpg","static/images/nanzhuang/man_6_8.jpg","static/images/nanzhuang/man_6_9.jpg","static/images/nanzhuang/man_6_10.jpg"]'
                             ),
                                          
                             (6, 123.00, 3, 
                              '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"48"}]',
                               '["static/images/nanzhuang/man_6_2_1.jpg","static/images/nanzhuang/man_6_2_2.jpg","static/images/nanzhuang/man_6_2_3.jpg"]'
                             ),
                             
                             (6, 123.00, 7, 
                              '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"50"}]',
                               '["static/images/nanzhuang/man_6_2_1.jpg","static/images/nanzhuang/man_6_2_2.jpg","static/images/nanzhuang/man_6_2_3.jpg"]'
                             ),
                             
                             (6, 123.00, 23, 
                              '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"52"}]',
                               '["static/images/nanzhuang/man_6_2_1.jpg","static/images/nanzhuang/man_6_2_2.jpg","static/images/nanzhuang/man_6_2_3.jpg"]'
                             ),
                             
                             (6, 123.00, 6, 
                              '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"54"}]',
                               '["static/images/nanzhuang/man_6_2_1.jpg","static/images/nanzhuang/man_6_2_2.jpg","static/images/nanzhuang/man_6_2_3.jpg"]'
                             ),
                             
                             (6, 123.00, 0, 
                              '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"56"}]',
                               '["static/images/nanzhuang/man_6_2_1.jpg","static/images/nanzhuang/man_6_2_2.jpg","static/images/nanzhuang/man_6_2_3.jpg"]'
                             ),
                             
                             (6, 123.00, 0, 
                              '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"58"}]',
                               '["static/images/nanzhuang/man_6_2_1.jpg","static/images/nanzhuang/man_6_2_2.jpg","static/images/nanzhuang/man_6_2_3.jpg"]'
                             ),
                             (6, 123.00, 7, 
                              '[{"attribute_id":1, "value":"深宝"}, {"attribute_id":2, "value":"54"}]',
                               '["static/images/nanzhuang/man_6_3_1.jpg","static/images/nanzhuang/man_6_3_2.jpg","static/images/nanzhuang/man_6_3_3.jpg"]'
                             )
                         """)
            #25春男式半高领针织提花开衫百搭外套
            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                     (7, 371.00, 13, 
                     '[{"attribute_id":1, "value":"藏青"}, {"attribute_id":2, "value":"48"}]',
                      '["static/images/nanzhuang/man_7_1.jpg","static/images/nanzhuang/man_7_2.jpg","static/images/nanzhuang/man_7_3.jpg","static/images/nanzhuang/man_7_4.jpg"]'
                     ),
                     (7, 371.00, 24, 
                     '[{"attribute_id":1, "value":"藏青"}, {"attribute_id":2, "value":"50"}]',
                      '["static/images/nanzhuang/man_7_1.jpg","static/images/nanzhuang/man_7_2.jpg","static/images/nanzhuang/man_7_3.jpg","static/images/nanzhuang/man_7_4.jpg"]'
                     ),
                     (7, 371.00, 39, 
                     '[{"attribute_id":1, "value":"藏青"}, {"attribute_id":2, "value":"52"}]',
                      '["static/images/nanzhuang/man_7_1.jpg","static/images/nanzhuang/man_7_2.jpg","static/images/nanzhuang/man_7_3.jpg","static/images/nanzhuang/man_7_4.jpg"]'
                     ),
                     (7, 371.00, 5, 
                     '[{"attribute_id":1, "value":"藏青"}, {"attribute_id":2, "value":"54"}]',
                      '["static/images/nanzhuang/man_7_1.jpg","static/images/nanzhuang/man_7_2.jpg","static/images/nanzhuang/man_7_3.jpg","static/images/nanzhuang/man_7_4.jpg"]'
                     ),
                     (7, 371.00, 3, 
                     '[{"attribute_id":1, "value":"藏青"}, {"attribute_id":2, "value":"54"}]',
                      '["static/images/nanzhuang/man_7_1.jpg","static/images/nanzhuang/man_7_2.jpg","static/images/nanzhuang/man_7_3.jpg","static/images/nanzhuang/man_7_4.jpg"]'
                     )                                      
            """)
            #女装
            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                       (8, 149.00, 23, 
                            '[{"attribute_id":1, "value":"咖啡"}, {"attribute_id":2, "value":"均码"}]',
                            '["static/images/nvzhuang/f_1_1.jpg","static/images/nvzhuang/f_1_2.jpg","static/images/nvzhuang/f_1_3.jpg","static/images/nvzhuang/f_1_4.jpg"]'
                        )
                                                                     
            """)

            cursor.execute("""
                     INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                         (9, 161.00, 34, 
                         '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"均码"}]',
                         '["static/images/nvzhuang/f_2_1.jpg","static/images/nvzhuang/f_2_2.jpg","static/images/nvzhuang/f_2_3.jpg","static/images/nvzhuang/f_2_4.jpg"]'
                        )

            """)

            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                        (10, 188.00, 1, 
                         '[{"attribute_id":1, "value":"米白"}, {"attribute_id":2, "value":"S"}]',
                         '["static/images/nvzhuang/f_3_1.jpg","static/images/nvzhuang/f_3_2.jpg","static/images/nvzhuang/f_3_3.jpg","static/images/nvzhuang/f_3_4.jpg"]'
                        ),
                        (10, 188.00, 12, 
                         '[{"attribute_id":1, "value":"米白"}, {"attribute_id":2, "value":"M"}]',
                         '["static/images/nvzhuang/f_3_1.jpg","static/images/nvzhuang/f_3_2.jpg","static/images/nvzhuang/f_3_3.jpg","static/images/nvzhuang/f_3_4.jpg"]'
                        )
            
            """)

            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                        (11, 543.00, 3, 
                         '[{"attribute_id":1, "value":"米白"}, {"attribute_id":2, "value":"M"}]',
                         '["static/images/nvzhuang/f_4_1.jpg","static/images/nvzhuang/f_4_2.jpg","static/images/nvzhuang/f_4_3.jpg","static/images/nvzhuang/f_4_4.jpg"]'
                        ),
                        (11, 543.00, 12, 
                         '[{"attribute_id":1, "value":"米白"}, {"attribute_id":2, "value":"L"}]',
                         '["static/images/nvzhuang/f_4_1.jpg","static/images/nvzhuang/f_4_2.jpg","static/images/nvzhuang/f_4_3.jpg","static/images/nvzhuang/f_4_4.jpg"]'
                        )
            
            """)

            #美妆
            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                        (12, 59.00, 1345, 
                         '[{"attribute_id":5, "value":"净含量"}, {"attribute_id":6, "value":"100g"}]',
                         '["static/images/meizhuang/m1_1.jpg","static/images/meizhuang/m1_2.jpg","static/images/meizhuang/m1_3.jpg","static/images/meizhuang/m1_4.jpg"]'
                        )
            """)

            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                        (13, 79.00, 2324, 
                         '[{"attribute_id":5, "value":"规格"}, {"attribute_id":6, "value":"30ml"}]',
                         '["static/images/meizhuang/m2_1.jpg","static/images/meizhuang/m2_2.jpg","static/images/meizhuang/m2_3.jpg","static/images/meizhuang/m2_4.jpg"]'
                        )
            """)
            #tongzhuang
            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                        (14, 84.55, 45, 
                         '[{"attribute_id":1, "value":"蓝色"}, {"attribute_id":2, "value":"S"}]',
                         '["static/images/tongzhuang/t1_1.jpg","static/images/tongzhuang/t1_2.jpg","static/images/tongzhuang/t1_3.jpg","static/images/tongzhuang/t1_4.jpg"]'
                  ),
                   (14, 84.55, 22, 
                         '[{"attribute_id":1, "value":"蓝色"}, {"attribute_id":2, "value":"M"}]',
                         '["static/images/tongzhuang/t1_1.jpg","static/images/tongzhuang/t1_2.jpg","static/images/tongzhuang/t1_3.jpg","static/images/tongzhuang/t1_4.jpg"]'
                  ),
                   (14, 84.55, 32, 
                         '[{"attribute_id":1, "value":"蓝色"}, {"attribute_id":2, "value":"L"}]',
                         '["static/images/tongzhuang/t1_1.jpg","static/images/tongzhuang/t1_2.jpg","static/images/tongzhuang/t1_3.jpg","static/images/tongzhuang/t1_4.jpg"]'
                  ),
                   (14, 84.55, 12, 
                         '[{"attribute_id":1, "value":"蓝色"}, {"attribute_id":2, "value":"XL"}]',
                         '["static/images/tongzhuang/t1_1.jpg","static/images/tongzhuang/t1_2.jpg","static/images/tongzhuang/t1_3.jpg","static/images/tongzhuang/t1_4.jpg"]'
                  ),
                   (14, 84.55, 9, 
                         '[{"attribute_id":1, "value":"蓝色"}, {"attribute_id":2, "value":"XXL"}]',
                         '["static/images/tongzhuang/t1_1.jpg","static/images/tongzhuang/t1_2.jpg","static/images/tongzhuang/t1_3.jpg","static/images/tongzhuang/t1_4.jpg"]'
                  )
            """)
            #男鞋
            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                   (15, 273.00, 43, 
                         '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"39"}]',
                         '["static/images/nanxie/nx1_1.jpg","static/images/nanxie/nx1_2.jpg","static/images/nanxie/nx1_3.jpg","static/images/nanxie/nx1_4.jpg"]'
                  ),
                  (15, 273.00, 23, 
                         '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"40"}]',
                         '["static/images/nanxie/nx1_1.jpg","static/images/nanxie/nx1_2.jpg","static/images/nanxie/nx1_3.jpg","static/images/nanxie/nx1_4.jpg"]'
                  )
            """)
            #女鞋
            cursor.execute("""
                 INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                   (16, 107.00, 22, 
                         '[{"attribute_id":1, "value":"米杏"}, {"attribute_id":2, "value":"35"}]',
                         '["static/images/nvxie/nx1_1.jpg","static/images/nvxie/nx1_2.jpg","static/images/nvxie/nx1_3.jpg","static/images/nvxie/nx1_4.jpg"]'
                  ),
                   (16, 107.00, 33, 
                         '[{"attribute_id":1, "value":"米杏"}, {"attribute_id":2, "value":"36"}]',
                         '["static/images/nvxie/nx1_1.jpg","static/images/nvxie/nx1_2.jpg","static/images/nvxie/nx1_3.jpg","static/images/nvxie/nx1_4.jpg"]'
                  ),
                   (16, 107.00, 45, 
                         '[{"attribute_id":1, "value":"米杏"}, {"attribute_id":2, "value":"37"}]',
                         '["static/images/nvxie/nx1_1.jpg","static/images/nvxie/nx1_2.jpg","static/images/nvxie/nx1_3.jpg","static/images/nvxie/nx1_4.jpg"]'
                  ),
                   (16, 107.00, 56, 
                         '[{"attribute_id":1, "value":"米杏"}, {"attribute_id":2, "value":"38"}]',
                         '["static/images/nvxie/nx1_1.jpg","static/images/nvxie/nx1_2.jpg","static/images/nvxie/nx1_3.jpg","static/images/nvxie/nx1_4.jpg"]'
                  ),
                   (16, 107.00, 23, 
                         '[{"attribute_id":1, "value":"米杏"}, {"attribute_id":2, "value":"39"}]',
                         '["static/images/nvxie/nx1_1.jpg","static/images/nvxie/nx1_2.jpg","static/images/nvxie/nx1_3.jpg","static/images/nvxie/nx1_4.jpg"]'
                  ),
                   (16, 107.00, 12, 
                         '[{"attribute_id":1, "value":"米杏"}, {"attribute_id":2, "value":"40"}]',
                         '["static/images/nvxie/nx1_1.jpg","static/images/nvxie/nx1_2.jpg","static/images/nvxie/nx1_3.jpg","static/images/nvxie/nx1_4.jpg"]'
                  )
            """)

            #内衣：
            cursor.execute("""
                INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                   (17, 75.00, 23, 
                         '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"M"}]',
                         '["static/images/neiyi/n2_1.jpg","static/images/neiyi/n2_2.jpg","static/images/neiyi/n2_3.jpg","static/images/neiyi/n2_4.jpg"]'
                  ),
                  (17, 75.00, 34, 
                         '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"L"}]',
                         '["static/images/neiyi/n2_1.jpg","static/images/neiyi/n2_2.jpg","static/images/neiyi/n2_3.jpg","static/images/neiyi/n2_4.jpg"]'
                  ),
                  (17, 75.00, 26, 
                         '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"XL"}]',
                         '["static/images/neiyi/n2_1.jpg","static/images/neiyi/n2_2.jpg","static/images/neiyi/n2_3.jpg","static/images/neiyi/n2_4.jpg"]'
                  ),
                  (17, 75.00, 3, 
                         '[{"attribute_id":1, "value":"白色"}, {"attribute_id":2, "value":"XXL"}]',
                         '["static/images/neiyi/n2_1.jpg","static/images/neiyi/n2_2.jpg","static/images/neiyi/n2_3.jpg","static/images/neiyi/n2_4.jpg"]'
                  )
                  
            """)

            #宠物
            cursor.execute("""
                 INSERT INTO sku (spu_id, price, stock, attributes, image) VALUES
                   (18, 22.00, 56, 
                         '[{"attribute_id":1, "value":""}, {"attribute_id":2, "value":"M(建议体重5~8斤)"}]',
                         '["static/images/congwu/w_1_1.jpg","static/images/congwu/w_1_2.jpg","static/images/congwu/w_1_3.jpg","static/images/congwu/w_1_4.jpg"]'
                  ),
                  (18, 22.00, 34, 
                         '[{"attribute_id":1, "value":""}, {"attribute_id":2, "value":"S(建议体重3~5斤)"}]',
                         '["static/images/congwu/w_1_1.jpg","static/images/congwu/w_1_2.jpg","static/images/congwu/w_1_3.jpg","static/images/congwu/w_1_4.jpg"]'
                  ),
                  (18, 22.00, 123, 
                         '[{"attribute_id":1, "value":""}, {"attribute_id":2, "value":"XS(建议体重1~3斤)"}]',
                         '["static/images/congwu/w_1_1.jpg","static/images/congwu/w_1_2.jpg","static/images/congwu/w_1_3.jpg","static/images/congwu/w_1_4.jpg"]'
                  )
            """)



        # 商品评价表（新增）
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS product_comment (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   spu_id INTEGER NOT NULL,
                   user_id INTEGER NOT NULL,
                   content TEXT NOT NULL,
                   rate INTEGER CHECK(rate BETWEEN 1 AND 5),  -- 评分1-5星
                   images TEXT,  -- JSON array
                   is_anonymous BOOLEAN DEFAULT 0,
                   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY (spu_id) REFERENCES spu(id),
                   FOREIGN KEY (user_id) REFERENCES users(id)
               )
           ''')

        # 购物车模块

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        sku_id INTEGER NOT NULL,
                        quantity INTEGER CHECK(quantity > 0),
                        selected BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (sku_id) REFERENCES sku(id)
                );
           """)

        # 订单模块
        cursor.execute("""
                CREATE TABLE  IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no TEXT NOT NULL UNIQUE,  -- 订单号
                    user_id INTEGER NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    payment_method INTEGER,  -- 支付方式 1-微信 2-支付宝
                    status INTEGER DEFAULT 1,  -- 1-待付款 2-已付款 3-已发货 4-已完成 5-已取消
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    pay_time DATETIME,  -- 新增支付时间
                    delivery_time DATETIME, -- 发货时间
                    finish_time DATETIME,  -- 完成时间
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
           """)

        cursor.execute("""
                CREATE TABLE  IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    sku_id INTEGER NOT NULL,
                    sku_name TEXT NOT NULL,
                    sku_image TEXT,
                    price DECIMAL(10,2) NOT NULL,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id)
                );
           """)

        cursor.execute("""           
                CREATE TABLE IF NOT EXISTS order_address (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id)
                );
           """)

        # 物流信息表（新增）
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS order_logistics (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   order_id INTEGER NOT NULL UNIQUE,
                   logistics_no TEXT NOT NULL,  -- 物流单号
                   company_code TEXT,  -- 物流公司编码
                   company_name TEXT,  -- 物流公司名称
                   receiver_name TEXT NOT NULL,
                   receiver_phone TEXT NOT NULL,
                   receiver_address TEXT NOT NULL,
                   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY (order_id) REFERENCES orders(id)
               )
           ''')

        # 支付记录表（新增）
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS payment_records (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   order_id INTEGER NOT NULL,
                   payment_no TEXT NOT NULL UNIQUE,  -- 支付平台交易号
                   amount DECIMAL(10,2) NOT NULL,
                   status INTEGER DEFAULT 0,  -- 0-待支付 1-支付成功 2-支付失败
                   payment_time DATETIME,
                   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY (order_id) REFERENCES orders(id)
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
                          ('static/images/carousel/carousol_3.jpg', '3·8换新节', '3·8换新节');
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
        # 请求格式验证
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['username', 'password', 'email', 'verification_code']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        username = data['username'].strip()
        password = data['password'].strip()
        email = data['email'].strip().lower()
        verification_code = data['verification_code'].strip()

        # 数据有效性验证
        if not all([username, password, email, verification_code]):
            return jsonify({"code": 400, "message": "字段不能为空"}), 400

        if len(password) < 8:
            return jsonify({"code": 400, "message": "密码长度至少8位"}), 400

        # 验证码校验
        stored_code = session.get('verification_code')
        stored_time = session.get('verification_code_time')
        if not stored_code or not stored_time:
            return jsonify({"code": 400, "message": "验证码无效"}), 400

        if datetime.now() - datetime.strptime(stored_time, '%Y-%m-%d %H:%M:%S') > timedelta(minutes=5):
            return jsonify({"code": 400, "message": "验证码已过期"}), 400

        if verification_code != stored_code:
            return jsonify({"code": 400, "message": "验证码错误"}), 400

        # 清理验证码
        session.pop('verification_code', None)
        session.pop('verification_code_time', None)

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                return jsonify({"code": 400, "message": "用户名或邮箱已存在"}), 400

            # 密码哈希处理
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # 创建用户
            cursor.execute("""
                INSERT INTO users (username, password, email, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, hashed_password, email, datetime.now(), datetime.now()))

            conn.commit()
            return jsonify({"code": 200, "message": "注册成功"}), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


# 登录接口
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        # 请求格式验证
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['username', 'password']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        username = data['username'].strip()
        password = data['password'].strip()

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 获取用户信息
            cursor.execute("""
                SELECT id, password, status FROM users 
                WHERE username = ? OR email = ?
            """, (username, username))

            user = cursor.fetchone()
            if not user:
                return jsonify({"code": 401, "message": "用户名或密码错误"}), 401

            # 检查账户状态
            if user['status'] == 0:
                return jsonify({"code": 403, "message": "账户已被禁用"}), 403

            # 密码验证
            if not check_password_hash(user['password'], password):
                return jsonify({"code": 401, "message": "用户名或密码错误"}), 401

            # 更新最后登录时间
            cursor.execute("""
                UPDATE users SET last_login = ?
                WHERE id = ?
            """, (datetime.now(), user['id']))
            conn.commit()

            # 生成访问令牌
            expires = timedelta(days=2)
            access_token = create_access_token(
                identity={
                    "user_id": user['id'],
                    "username": username
                },
                expires_delta=expires
            )

            return jsonify({
                "code": 200,
                "message": "登录成功",
                "data": {
                    "access_token": access_token,
                    "user_id": user['id']
                }
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


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


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 查询用户基本信息
            cursor.execute('''
                SELECT id, username, email, phone, avatar, gender, status, last_login, created_at, updated_at, is_deleted
                FROM users
                WHERE id = ?
            ''', (user_id,))
            user_data = cursor.fetchone()

            if not user_data:
                return jsonify({
                    "code": 404,
                    "data": None,
                    "message": "用户不存在"
                }), 404

            # 查询用户地址信息
            cursor.execute('''
                SELECT id, name, phone, province, city, district, detail, is_default, created_at
                FROM user_address
                WHERE user_id = ?
            ''', (user_id,))
            addresses_data = [dict(row) for row in cursor.fetchall()]

            # 构建最终的用户详细信息
            user_details = {
                "id": user_data['id'],
                "username": user_data['username'],
                "email": user_data['email'],
                "phone": user_data['phone'],
                "avatar": user_data['avatar'],
                "gender": user_data['gender'],
                "status": user_data['status'],
                "last_login": user_data['last_login'],
                "created_at": user_data['created_at'],
                "updated_at": user_data['updated_at'],
                "is_deleted": user_data['is_deleted'],
                "addresses": addresses_data
            }

            return jsonify({
                "code": 200,
                "data": user_details,
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





#商品接口
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 获取SPU基础信息
            cursor.execute('''
                SELECT spu.*, brands.name as brand_name, categories.name as category_name 
                FROM spu 
                JOIN brands ON spu.brand_id = brands.id
                JOIN categories ON spu.category_id = categories.id
            ''')
            spu_list = [dict(row) for row in cursor.fetchall()]

            # 获取SKU详细信息
            for spu in spu_list:
                cursor.execute('''
                    SELECT * FROM sku WHERE spu_id = ?
                ''', (spu['id'],))
                spu['skus'] = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "code": 200,
                "data": {"items":spu_list},
                "message": "Success"
            })

    except sqlite3.Error as e:
        app.logger.error(f"获取商品失败: {str(e)}")
        return jsonify({"code": 500, "message": "数据库错误"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


@app.route('/api/brands/<int:brand_id>/products', methods=['GET'])
def get_products_by_brand(brand_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 获取SPU基础信息
            cursor.execute('''
                SELECT spu.*, brands.name as brand_name, categories.name as category_name 
                FROM spu 
                JOIN brands ON spu.brand_id = brands.id
                JOIN categories ON spu.category_id = categories.id
                WHERE spu.brand_id = ?
            ''', (brand_id,))
            spu_list = [dict(row) for row in cursor.fetchall()]

            # 获取SKU详细信息
            for spu in spu_list:
                cursor.execute('''
                    SELECT * FROM sku WHERE spu_id = ?
                ''', (spu['id'],))
                spu['skus'] = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "code": 200,
                "data": {"items": spu_list},
                "message": "Success"
            })

    except sqlite3.Error as e:
        app.logger.error(f"获取品牌商品失败: {str(e)}")
        return jsonify({"code": 500, "message": "数据库错误"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

@app.route('/api/hot_products', methods=['GET'])
def get_hot_products():
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 获取SPU基础信息，只获取热销商品
            cursor.execute('''
                SELECT spu.*, brands.name as brand_name, categories.name as category_name 
                FROM spu 
                JOIN brands ON spu.brand_id = brands.id
                JOIN categories ON spu.category_id = categories.id
                WHERE spu.is_hot = 1
            ''')
            spu_list = [dict(row) for row in cursor.fetchall()]

            # 获取SKU详细信息
            for spu in spu_list:
                cursor.execute('''
                    SELECT * FROM sku WHERE spu_id = ?
                ''', (spu['id'],))
                spu['skus'] = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "code": 200,
                "data": {"items": spu_list},
                "message": "Success"
            })

    except sqlite3.Error as e:
        app.logger.error(f"获取热销商品失败: {str(e)}")
        return jsonify({"code": 500, "message": "数据库错误"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


@app.route('/api/products/<int:spu_id>/sizes', methods=['GET'])
def get_product_sizes(spu_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 获取SKU详细信息，只获取尺寸或尺码属性
            cursor.execute('''
                SELECT attributes FROM sku WHERE spu_id = ?
            ''', (spu_id,))
            sku_list = cursor.fetchall()

            # 提取尺寸或尺码信息
            sizes = set()
            for sku in sku_list:
                attributes = eval(sku['attributes'])# 将JSON字符串转换为Python列表
                for attribute in attributes:
                    if attribute['attribute_id'] == 2:
                        sizes.add(attribute['value'])


            return jsonify({
                "code": 200,
                "data": {"sizes": list(sizes)},
                "message": "Success"
            })

    except sqlite3.Error as e:
        app.logger.error(f"获取商品尺寸或尺码失败: {str(e)}")
        return jsonify({"code": 500, "message": "数据库错误"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500



@app.route('/api/products/<int:spu_id>/colors', methods=['GET'])
def get_product_colors(spu_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 获取SKU详细信息，只获取颜色属性
            cursor.execute('''
                SELECT attributes FROM sku WHERE spu_id = ?
            ''', (spu_id,))
            sku_list = cursor.fetchall()

            # 提取颜色信息
            colors = set()
            for sku in sku_list:
                attributes = eval(sku['attributes'])# 将JSON字符串转换为Python列表
                for attribute in attributes:
                    if attribute['attribute_id'] == 1:
                        colors.add(attribute['value'])

            return jsonify({
                "code": 200,
                "data": {"colors": list(colors)},
                "message": "Success"
            })

    except sqlite3.Error as e:
        app.logger.error(f"获取商品颜色失败: {str(e)}")
        return jsonify({"code": 500, "message": "数据库错误"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


@app.route('/api/products/<int:spu_id>', methods=['GET'])
def get_product_details(spu_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 获取SPU基础信息
            cursor.execute('''
                SELECT spu.*, brands.name as brand_name, categories.name as category_name 
                FROM spu 
                JOIN brands ON spu.brand_id = brands.id
                JOIN categories ON spu.category_id = categories.id
                WHERE spu.id = ?
            ''', (spu_id,))
            spu_data = cursor.fetchone()

            if not spu_data:
                return jsonify({
                    "code": 404,
                    "data": None,
                    "message": "商品不存在"
                }), 404

            # 获取SKU详细信息
            cursor.execute('''
                SELECT * FROM sku WHERE spu_id = ?
            ''', (spu_id,))
            sku_list = [dict(row) for row in cursor.fetchall()]

            # 将SKU信息中的attributes字段从JSON字符串转换为Python列表
            for sku in sku_list:
                sku['attributes'] = json.loads(sku['attributes'])

            # 构建最终的商品详细信息
            product_details = {
                "id": spu_data['id'],
                "name": spu_data['name'],
                "description": spu_data['description'],
                "main_image": spu_data['main_image'],
                "detail_images": json.loads(spu_data['detail_images']),
                "sales_count": spu_data['sales_count'],
                "review_count": spu_data['review_count'],
                "status": spu_data['status'],
                "created_at": spu_data['created_at'],
                "updated_at": spu_data['updated_at'],
                "is_hot": spu_data['is_hot'],
                "brand_name": spu_data['brand_name'],
                "category_name": spu_data['category_name'],
                "skus": sku_list
            }

            return jsonify({
                "code": 200,
                "data": product_details,
                "message": "Success"
            })

    except sqlite3.Error as e:
        app.logger.error(f"获取商品详细信息失败: {str(e)}")
        return jsonify({"code": 500, "message": "数据库错误"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500





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



@app.route('/api/brands', methods=['GET'])
def get_brands():
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 查询所有品牌数据
            cursor.execute('''
                SELECT id, name, logo, story, backimg,sort_order, is_recommend 
                FROM brands 
                ORDER BY sort_order ASC
            ''')
            brands_data = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "code": 200,
                "data": {"data": brands_data},
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


@app.route('/api/categories/<int:category_id>/products', methods=['GET'])
def get_products_by_category(category_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 获取SPU基础信息
            cursor.execute('''
                SELECT spu.*, brands.name as brand_name, categories.name as category_name 
                FROM spu 
                JOIN brands ON spu.brand_id = brands.id
                JOIN categories ON spu.category_id = categories.id
                WHERE spu.category_id = ?
            ''', (category_id,))
            spu_list = [dict(row) for row in cursor.fetchall()]

            # 获取SKU详细信息
            for spu in spu_list:
                cursor.execute('''
                    SELECT * FROM sku WHERE spu_id = ?
                ''', (spu['id'],))
                spu['skus'] = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "code": 200,
                "data": {"items": spu_list},
                "message": "Success"
            })

    except sqlite3.Error as e:
        app.logger.error(f"获取分类商品失败: {str(e)}")
        return jsonify({"code": 500, "message": "数据库错误"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True)



























