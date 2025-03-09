import csv
import json
import random
from flask import Flask, session, request, jsonify, make_response
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import *
import  string
import os
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler





app = Flask(__name__)


# 设置session密钥
app.config['SECRET_KEY'] = 'your-strong-secret-key'



UPLOAD_FOLDER = 'static/images/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))







# 配置数据库
import sqlite3

DATABASE = 'database.db'


def init_db():
    # 链接数据库db = SQLite3
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        cursor.execute('''
                   CREATE TABLE IF NOT EXISTS advertisements (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       image TEXT NOT NULL,  -- 图片URL
                       description TEXT NOT NULL  -- 文字描述
                   );
        ''')

        # 地理位置表


        # 用户表优化
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT NOT NULL UNIQUE,
                   password TEXT NOT NULL,
                   phone TEXT DEFAULT '13200984321',
                   avatar TEXT DEFAULT '/static/images/touxiang.png',
                   gender INTEGER DEFAULT 1 CHECK(gender IN (0,1,2)),
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
                   province TEXT ,
                   city TEXT ,
                   district TEXT ,
                   detail TEXT  ,
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
                                    ('嬉皮狗','static/images/BrandLogo/嬉皮狗/logo.png','','/static/images/BrandLogo/嬉皮狗/back.png'),
                                    ('ZHR则则','static/images/BrandLogo/ZHR则则/logo.png','ZHR是一家注重脚感和细节的有态度的品牌：品牌专注于女鞋，通过充满时尚感的设计、高舒适度的穿着体验、符合人体工学的设计原理，为顾客呈现高性价比的优质产品。','static/images/BrandLogo/ZHR则则/back.jpg'),
                                    ('unkown','static/images/BrandLogo/ZHR则则/logo.png','','static/images/BrandLogo/ZHR则则/back.jpg');
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
                        sales_count INTEGER DEFAULT 0,
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
                   username TEXT,
                   spu_id INTEGER NOT NULL,
                   user_id INTEGER NOT NULL,
                   content TEXT NOT NULL,
                   rate INTEGER CHECK(rate BETWEEN 1 AND 5),  -- 评分1-5星
                   touxiang TEXT DEFAULT 'http://127.0.0.1:5000/static/images/touxiang.png',
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
                    payment_method INTEGER DEFAULT 0,  -- 支付方式 1-微信 2-支付宝 0-未支付
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

        # 订单地址表
        # 订单地址表
        cursor.execute('''           
                  CREATE TABLE IF NOT EXISTS order_address (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      order_id INTEGER NOT NULL,
                      user_id INTEGER NOT NULL,
                      address_id INTEGER NOT NULL,
                      FOREIGN KEY (order_id) REFERENCES orders(id),
                      FOREIGN KEY (user_id) REFERENCES users(id),
                      FOREIGN KEY (address_id) REFERENCES user_address(id)
                  );
              ''')

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

#模拟用户数据
def insert_sample_users():
    sample_users = [
        {
            'username': 'feiniao1',
            'id':1,
            'password': '12345678',

            'phone': '13200984321',
            'avatar': '/static/images/commonet/touxiang1.jpeg',
            'gender': 1,  # 1 - 男
            'status': 1,
            'last_login': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'is_deleted': 0
        },
        {
            'username': 'feiniao2',
            'id': 2,
            'password': '12345678',

            'phone': '13200984322',
            'avatar': '/static/images/commonet/touxiang2.png',
            'gender': 2,  # 2 - 女
            'status': 1,
            'last_login': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'is_deleted': 0
        },
        {
            'username': 'feiniao3',
            'id': 3,
            'password': '12345678',
            'phone': '13200984323',
            'avatar': '/static/images/commonet/touxiangh3.jpeg',
            'gender': 0,  # 0 - 未知
            'status': 1,
            'last_login': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'is_deleted': 0
        }
    ]

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()


        for user in sample_users:
            # 检查用户是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (user['username'],))
            if cursor.fetchone():
                continue

            hashed_password = generate_password_hash(user['password'], method='pbkdf2:sha256')
            cursor.execute('''
                INSERT INTO users (id,username, password, phone, avatar, gender, status, last_login, created_at, updated_at, is_deleted)
                VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user['id'],
                user['username'],
                hashed_password,
                user['phone'],
                user['avatar'],
                user['gender'],
                user['status'],
                user['last_login'],
                user['created_at'],
                user['updated_at'],
                user['is_deleted']
            ))
        conn.commit()


def insert_pinlun():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # 插入模拟评论数据
        cursor.execute('''
            SELECT COUNT(*) FROM product_comment
        ''')
        if cursor.fetchone()[0] == 0:
            # 预定义的评论内容
            comments = [
                "质量很好，物超所值！",
                "款式时尚，非常喜欢！",
                "尺码标准，穿着舒适",
                "颜色和图片一致，满意",
                "发货速度快，服务好",
                "面料手感不错，值得购买",
                "设计独特，朋友都说好看",
                "性价比很高，推荐购买",
                "细节处理得很好，做工精细",
                "第二次购买了，一如既往的好"
            ]
            # 获取所有SPU ID
            cursor.execute("SELECT id FROM spu")
            spu_ids = [row[0] for row in cursor.fetchall()]

            # 获取所有用户ID
            cursor.execute("SELECT id FROM users")
            user_ids = [row[0] for row in cursor.fetchall()]
            # 为每个SPU插入2条评论
            for spu_id in spu_ids:
                for _ in range(2):
                    # 随机选择用户和评论内容
                    user_id = random.choice(user_ids)

                    cursor.execute("SELECT avatar FROM users WHERE id = ?", (user_id,))
                    avatar = cursor.fetchone()[0]

                    content = random.choice(comments)
                    rate = random.randint(4, 5)  # 评分4-5分
                    is_anonymous = random.choice([0, 1])
                    if is_anonymous == 1:
                        username = "匿名用户"
                    else:
                        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                        username = cursor.fetchone()[0]

                    cursor.execute('''
                        INSERT INTO product_comment
                        (username,spu_id, user_id, content, rate, touxiang,is_anonymous, created_at)
                        VALUES (?,?, ?, ?, ?, ?,?, ?)
                    ''', (
                        username,
                        spu_id,
                        user_id,
                        content,
                        rate,
                        avatar,
                        is_anonymous,
                        datetime.now() - timedelta(days=random.randint(1, 30))
                    ))

            conn.commit()

def insert_sample_advertisements():
    sample_advertisements = [
        {
            'image': 'static/images/advertise/i1.jpeg',
            'description': '灵感穿搭1折起'
        },
        {
            'image': 'static/images/advertise/i2.jpeg',
            'description': '神仙水买230ml至高享390ml'
        },
        {
            'image': 'static/images/advertise/i3.jpeg',
            'description': '3·8换新节'
        },
        {
            'image': 'static/images/advertise/i4.jpg',
            'description': '3·8换新节'
        }
    ]

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # 插入模拟地址数据
        cursor.execute('''
                  SELECT COUNT(*) FROM advertisements
              ''')
        if cursor.fetchone()[0] == 0:
            for ad in sample_advertisements:
                cursor.execute('''
                           INSERT INTO advertisements (image, description)
                           VALUES (?, ?)
                       ''', (ad['image'], ad['description']))
        conn.commit()


def insert_sample_user_addresses():
    sample_addresses = [
        {
            'user_id': 1,
            'name': '张三',
            'phone': '13800138000',
            'province': '广东省',
            'city': '广州市',
            'district': '天河区',
            'detail': '天河路123号',
            'is_default': 1,
            'created_at': datetime.now()
        },
        {
            'user_id': 1,
            'name': '李四',
            'phone': '13900139000',
            'province': '广东省',
            'city': '深圳市',
            'district': '南山区',
            'detail': '科技园456号',
            'is_default': 0,
            'created_at': datetime.now()
        },
        {
            'user_id': 2,
            'name': '王五',
            'phone': '13700137000',
            'province': '江苏省',
            'city': '南京市',
            'district': '玄武区',
            'detail': '玄武大道789号',
            'is_default': 1,
            'created_at': datetime.now()
        },
        {
            'user_id': 2,
            'name': '赵六',
            'phone': '13600136000',
            'province': '江苏省',
            'city': '苏州市',
            'district': '姑苏区',
            'detail': '姑苏路101号',
            'is_default': 0,
            'created_at': datetime.now()
        },
        {
            'user_id': 3,
            'name': '孙七',
            'phone': '13500135000',
            'province': '浙江省',
            'city': '杭州市',
            'district': '西湖区',
            'detail': '西湖路202号',
            'is_default': 1,
            'created_at': datetime.now()
        }
    ]

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # 插入模拟地址数据
        cursor.execute('''
            SELECT COUNT(*) FROM user_address
        ''')
        if cursor.fetchone()[0] == 0:
            for address in sample_addresses:
                cursor.execute('''
                    INSERT INTO user_address (user_id, name, phone, province, city, district, detail, is_default, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    address['user_id'],
                    address['name'],
                    address['phone'],
                    address['province'],
                    address['city'],
                    address['district'],
                    address['detail'],
                    address['is_default'],
                    address['created_at']
                ))

        conn.commit()

def insert_sample_cart_items():
    sample_cart_items = [
        {
            'user_id': 1,
            'id': 1,
            'sku_id': 1,
            'quantity': 2
        },
        {
            'user_id': 1,
            'id': 2,
            'sku_id': 3,
            'quantity': 1
        },
        {
            'user_id': 2,
            'id': 3,
            'sku_id': 5,
            'quantity': 3
        },
        {
            'user_id': 2,
            'id': 4,
            'sku_id': 7,
            'quantity': 1
        },
        {
            'user_id': 3,
            'id': 5,
            'sku_id': 9,
            'quantity': 2
        },
        {
            'user_id': 3,
            'id': 6,
            'sku_id': 11,
            'quantity': 1
        }
    ]

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # 插入模拟购物车数据
        cursor.execute('''
            SELECT COUNT(*) FROM cart
        ''')
        if cursor.fetchone()[0] == 0:
            for item in sample_cart_items:
                cursor.execute('''INSERT INTO cart (id,user_id, sku_id, quantity) VALUES (?,?, ?, ?)''',
                               (item['id'],item['user_id'], item['sku_id'], item['quantity']))

        conn.commit()


def insert_location():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            # 清空 locations 表
            cursor.execute("DELETE FROM locations")

            # 执行 SQL 脚本
            with open('location.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
                cursor.executescript(sql_script)

        except Exception as e:
            print(f"Error executing location.sql: {str(e)}")



def create_tables():
    init_db()  # 先创建表结构
    insert_sample_users()  # 其他数据初始化
    # 添加延迟确保locations表已创建
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: init_db(),  # 再次执行确保数据插入
        'date',
        run_date=datetime.now() + timedelta(seconds=5)
    )
    scheduler.start()




@app.before_request
def create_tables():
    init_db()
    insert_sample_users()
    insert_pinlun()
    insert_sample_advertisements()
    insert_sample_user_addresses()
    insert_sample_cart_items()
    insert_location()






def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# 1. 图片上传接口
@app.route('/api/upload_avatar', methods=['POST'])
def upload_avatar():
    try:
        if 'file' not in request.files:
            return jsonify({"code": 400, "message": "没有文件部分"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"code": 400, "message": "没有选择文件"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return jsonify({
                "code": 200,
                "data": {
                    "url": f"/{file_path}"
                },
                "message": "文件上传成功"
            }), 200

        return jsonify({"code": 400, "message": "文件类型不允许"}), 400

    except Exception as e:
        app.logger.error(f"上传文件异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


# 2.用户更改头像接口
@app.route('/api/users/<int:user_id>/avatar', methods=['PUT'])
def update_user_avatar(user_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        avatar_url = data.get('avatar_url')
        if not avatar_url:
            return jsonify({"code": 400, "message": "缺少avatar_url字段"}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 更新用户头像URL
            cursor.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar_url, user_id))
            conn.commit()

            return jsonify({
                "code": 200,
                "message": "用户头像更新成功"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

#获取用户的地址列表
@app.route('/api/users/<int:user_id>/addresses', methods=['GET'])
def get_user_addresses(user_id):
    """获取用户地址列表接口"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 查询地址信息
            cursor.execute('''
                SELECT 
                    id,
                    name,
                    phone,
                    province,
                    city,
                    district,
                    detail,
                    is_default,
                    created_at
                FROM user_address 
                WHERE user_id = ?
                ORDER BY is_default DESC, created_at DESC
            ''', (user_id,))

            addresses = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "code": 200,
                "data": {
                    "items": addresses
                },
                "message": "获取地址成功"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

# 删除用户地址
@app.route('/api/users/<int:user_id>/addresses/<int:address_id>', methods=['DELETE'])
def delete_user_address(user_id, address_id):
    """删除用户地址接口"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证地址归属
            cursor.execute('''
                SELECT id, is_default 
                FROM user_address 
                WHERE id = ? AND user_id = ?
            ''', (address_id, user_id))
            address = cursor.fetchone()

            if not address:
                return jsonify({"code": 404, "message": "地址不存在或不属于您"}), 404

            # 检查关联订单（根据order_address表关联）
            cursor.execute('''
                SELECT order_id 
                FROM order_address 
                WHERE address_id = ?
                LIMIT 1
            ''', (address_id,))
            if cursor.fetchone():
                return jsonify({"code": 409, "message": "该地址已被订单使用，不可删除"}), 409

            # 执行删除操作
            cursor.execute('''
                DELETE FROM user_address 
                WHERE id = ? AND user_id = ?
            ''', (address_id, user_id))

            # 如果删除的是默认地址，设置最新地址为默认（可选）
            if address[1] == 1:
                # 先查询最新地址
                cursor.execute('''
                    SELECT id 
                    FROM user_address 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (user_id,))
                latest_address = cursor.fetchone()

                # 如果存在其他地址才更新
                if latest_address:
                    cursor.execute('''
                        UPDATE user_address 
                        SET is_default = 1 
                        WHERE id = ? AND user_id = ?
                    ''', (latest_address[0], user_id))

            conn.commit()
            return jsonify({
                "code": 200,
                "message": "地址删除成功"
            }), 200

    except sqlite3.Error as e:
        conn.rollback()
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


#添加用户地址
@app.route('/api/users/<int:user_id>/addresses', methods=['POST'])
def add_user_address(user_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['name', 'phone', 'province', 'city', 'district', 'detail']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        name = data['name'].strip()
        phone = data['phone'].strip()
        province = data['province'].strip()
        city = data['city'].strip()
        district = data['district'].strip()
        detail = data['detail'].strip()
        is_default = data.get('is_default', 0)  # 默认为0，即非默认地址

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 插入新地址
            cursor.execute('''
                INSERT INTO user_address (
                    user_id, name, phone, province, 
                    city, district, detail, is_default, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                name,
                phone,
                province,
                city,
                district,
                detail,
                is_default,
                datetime.now()
            ))

            # 获取新插入的地址ID
            address_id = cursor.lastrowid

            # 如果新地址设置为默认地址，更新其他地址为非默认
            if is_default:
                cursor.execute('''
                    UPDATE user_address 
                    SET is_default = 0 
                    WHERE user_id = ? AND id != ?
                ''', (user_id, address_id))

            conn.commit()

            # 查询新插入的地址信息
            cursor.execute('''
                SELECT * FROM user_address WHERE id = ?
            ''', (address_id,))
            address = cursor.fetchone()

            return jsonify({
                "code": 200,
                "data": None,
                "message": "地址添加成功"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

#修改用户地址
@app.route('/api/users/<int:user_id>/addresses/<int:address_id>', methods=['PUT'])
def update_user_address(user_id, address_id):
    """更新用户地址接口"""
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        # 校验必要字段
        required_fields = ['name', 'phone', 'province', 'city', 'district', 'detail']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        # 提取并处理参数
        name = data['name'].strip()
        phone = data['phone'].strip()
        province = data['province'].strip()
        city = data['city'].strip()
        district = data['district'].strip()
        detail = data['detail'].strip()
        is_default = data.get('is_default', 0)

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证地址归属
            cursor.execute('''
                SELECT id, is_default 
                FROM user_address 
                WHERE id = ? AND user_id = ?
            ''', (address_id, user_id))
            address = cursor.fetchone()

            if not address:
                return jsonify({"code": 404, "message": "地址不存在或不属于您"}), 404

            # 执行更新操作
            cursor.execute('''
                UPDATE user_address SET
                    name = ?,
                    phone = ?,
                    province = ?,
                    city = ?,
                    district = ?,
                    detail = ?,
                    is_default = ?
                WHERE id = ? AND user_id = ?
            ''', (
                name, phone, province, city, district, detail,
                is_default, address_id, user_id
            ))

            # 处理默认地址逻辑
            if is_default:
                cursor.execute('''
                    UPDATE user_address 
                    SET is_default = 0 
                    WHERE user_id = ? AND id != ?
                ''', (user_id, address_id))

            conn.commit()

            # 查询更新后的地址信息
            cursor.execute('''
                SELECT * FROM user_address 
                WHERE id = ? AND user_id = ?
            ''', (address_id, user_id))
            updated_address = cursor.fetchone()

            return jsonify({
                "code": 200,
                "data": None,
                "message": "地址更新成功"
            }), 200

    except sqlite3.Error as e:
        conn.rollback()
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

#设置默认地址
@app.route('/api/users/<int:user_id>/addresses/<int:address_id>/default', methods=['PUT'])
def set_default_address(user_id, address_id):
    """设置默认地址接口"""
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证地址有效性
            cursor.execute('''
                SELECT id 
                FROM user_address 
                WHERE id = ? AND user_id = ?
            ''', (address_id, user_id))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "地址不存在或不属于您"}), 404

            # 开启事务
            cursor.execute("BEGIN TRANSACTION")

            # 重置所有地址为非默认
            cursor.execute('''
                UPDATE user_address 
                SET is_default = 0 
                WHERE user_id = ?
            ''', (user_id,))

            # 设置当前地址为默认
            cursor.execute('''
                UPDATE user_address 
                SET is_default = 1 
                WHERE id = ? AND user_id = ?
            ''', (address_id, user_id))

            conn.commit()

            return jsonify({
                "code": 200,
                "message": "默认地址设置成功",
                "data": None
            }), 200

    except sqlite3.Error as e:
        conn.rollback()
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500



#更新y用户详细信息
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_details(user_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        # 验证用户是否存在
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 提取可更新的字段
            update_fields = {
                'username': data.get('username'),
                'phone': data.get('phone'),
                'gender': data.get('gender'),
                'avatar': data.get('avatar')
            }

            # 构建SQL更新语句
            set_clause = ', '.join([f"{key} = ?" for key in update_fields if update_fields[key] is not None])
            values = [value for value in update_fields.values() if value is not None]
            values.append(user_id)

            if not set_clause:
                return jsonify({"code": 400, "message": "没有提供可更新的字段"}), 400

            sql = f"UPDATE users SET {set_clause} WHERE id = ?"
            cursor.execute(sql, values)
            conn.commit()

            # 返回更新后的用户信息
            cursor.execute('''
                SELECT 
                    id, 
                    username, 
                    phone, 
                    avatar, 
                    gender, 
                    status, 
                    strftime('%Y-%m-%dT%H:%M:%SZ', last_login) as last_login,
                    strftime('%Y-%m-%dT%H:%M:%SZ', created_at) as created_at,
                    strftime('%Y-%m-%dT%H:%M:%SZ', updated_at) as updated_at, 
                    is_deleted
                FROM users
                WHERE id = ?
            ''', (user_id,))
            user_data = cursor.fetchone()

            return jsonify({
                "code": 200,
                "data": dict(user_data),
                "message": "用户信息更新成功"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500





@app.route('/api/random_products', methods=['GET'])
def get_random_products():
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 获取所有SPU的ID
            cursor.execute("SELECT id FROM spu")
            spu_ids = [row['id'] for row in cursor.fetchall()]

            # 随机选择一些SPU ID
            selected_spu_ids = random.sample(spu_ids, min(10, len(spu_ids)))  # 假设随机选择最多10个商品

            # 获取选中的SPU基础信息
            cursor.execute('''
                SELECT spu.*, brands.name as brand_name, categories.name as category_name 
                FROM spu 
                JOIN brands ON spu.brand_id = brands.id
                JOIN categories ON spu.category_id = categories.id
                WHERE spu.id IN ({})
            '''.format(','.join('?' for _ in selected_spu_ids)), selected_spu_ids)
            spu_list = [dict(row) for row in cursor.fetchall()]

            # 获取每个SPU的SKU详细信息
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





@app.route('/api/advertisements', methods=['GET'])
def get_advertisements():
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 查询所有广告数据
            cursor.execute('''
                SELECT * FROM advertisements
            ''')
            advertisements_data = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "code": 200,
                "data": {"items":advertisements_data,
                         "isshow":True,
                         "showTime":10
                         },
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


@app.route("/get_verification_code", methods=["GET"])
def get_verification_code():
    try:
        code = generate_verification_code()
        session['verification_code'] = code
        session['verification_code_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response = jsonify({
            "code": 200,
            "data": {"verification_code": code},
            "message": "Success"
        })
        return response
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


@app.route('/api/locations/<int:parent_id>', methods=['GET'])
def get_locations_by_parent(parent_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, name, parent_id 
                FROM locations 
                WHERE parent_id = ?
                ORDER BY id
            ''', (parent_id,))

            return jsonify({
                "code": 200,
                "data": [dict(row) for row in cursor.fetchall()],
                "message": "Success"
            })

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500




@app.route('/api/locations', methods=['GET'])
def get_locations():
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 查询所有省份
            cursor.execute('''
                SELECT id, name, parent_id 
                FROM locations 
                WHERE parent_id = 0
                ORDER BY name ASC
            ''')
            provinces = [dict(row) for row in cursor.fetchall()]

            # 查询所有城市
            cursor.execute('''
                SELECT id, name, parent_id 
                FROM locations 
                WHERE parent_id != 0
                ORDER BY name ASC
            ''')
            cities = [dict(row) for row in cursor.fetchall()]

            # 构建省份和城市的关系
            for province in provinces:
                province['cities'] = [city for city in cities if city['parent_id'] == province['id']]

            return jsonify({
                "code": 200,
                "data": {"items":provinces},
                "message": "Success"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"获取地理位置失败: {str(e)}")
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
            return jsonify({"code": 400, "message": "请求格式错误"}), 401

        required_fields = ['username', 'password', 'verification_code']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 402

        username = data['username'].strip()
        password = data['password'].strip()
        verification_code = data['verification_code'].strip()

        # 数据有效性验证
        if not all([username, password, verification_code]):
            return jsonify({"code": 400, "message": "字段不能为空"}), 403

        if len(password) < 8:
            return jsonify({"code": 400, "message": "密码长度至少8位"}), 404

        # 验证码校验
        stored_code = session.get('verification_code')
        stored_time = session.get('verification_code_time')
        print('----->',stored_code, stored_time)
        if not stored_code or not stored_time:
            return jsonify({"code": 400, "message": "验证码无效"}), 405

        if datetime.now() - datetime.strptime(stored_time, '%Y-%m-%d %H:%M:%S') > timedelta(minutes=5):
            return jsonify({"code": 400, "message": "验证码已过期"}), 406

        if verification_code != stored_code:
            return jsonify({"code": 400, "message": "验证码错误"}), 407

        # 清理验证码
        session.pop('verification_code', None)
        session.pop('verification_code_time', None)

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return jsonify({"code": 400, "message": "用户名或邮箱已存在"}), 408

            # 密码哈希处理
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # 创建用户
            cursor.execute("""
                INSERT INTO users (username, password, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (username, hashed_password, datetime.now(), datetime.now()))

            conn.commit()
            return jsonify({"code": 200,"data":None, "message": "注册成功"}), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 501
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 502


# 登录接口
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['username', 'password']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        username = data['username'].strip()
        password = data['password'].strip()

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能

            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,))
            user = cursor.fetchone()

            if not user:
                return jsonify({"code": 401, "message": "用户名或密码错误"}), 401

            if not check_password_hash(user['password'], password):
                return jsonify({"code": 401, "message": "用户名或密码错误"}), 401

                # +++ 新增开始：更新最后登录时间 +++
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(), user['id'])
            )
            conn.commit()
                # +++ 新增结束 +++

            if user['status'] == 0:
                return jsonify({"code": 403, "message": "账户已被禁用"}), 403





            return jsonify({
                "code": 200,
                "message": "登录成功",
                "data": {
                    "user_id": user['id']  # 返回数值型ID
                }
            }), 200

    except Exception as e:
        app.logger.error(f"登录异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500




# 获取用户详细信息
@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    try:

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 查询用户基本信息
            cursor.execute('''
                SELECT 
                id, 
                username, 
                phone, 
                avatar, 
                gender, 
                status, 
                strftime('%Y-%m-%dT%H:%M:%SZ', last_login) as last_login,
                strftime('%Y-%m-%dT%H:%M:%SZ', created_at) as created_at,
                strftime('%Y-%m-%dT%H:%M:%SZ', updated_at) as updated_at, 
                is_deleted
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
                SELECT id, 
                name, 
                phone, 
                province || city || district || detail as full_address,
                is_default, 
                strftime('%Y-%m-%dT%H:%M:%SZ', created_at) as created_at
                FROM user_address
                WHERE user_id = ?
            ''', (user_id,))
            addresses_data = []

            for row in cursor.fetchall():
                addr = dict(row)
                addresses_data.append({
                    "id": addr['id'],
                    "name": addr['name'],
                    "phone": addr['phone'],
                    "full_address": addr['full_address'],
                    "is_default": bool(addr['is_default']),
                    "created_at": addr['created_at']
                })

            return jsonify({
                "code": 200,
                "data": {
                    **dict(user_data),
                    "gender": ["未知", "男", "女"][user_data['gender']],  # 转换性别显示
                    "addresses": addresses_data
                },
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

# 根据品牌ID获取商品
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


# 获取热销商品
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

# 获取商品尺寸或尺码
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


#获取商品颜色
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

# 获取某件商品详情
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




# 获取所有分类
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


# 获取所有品牌
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
                "data":  brands_data,
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

#获取分类下的商品
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




##########评论接口
#创建评论接口
@app.route('/api/products/<int:spu_id>/comments/<int:user_id>', methods=['POST'])
def create_product_comment(spu_id, user_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['content', 'rate']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        content = data['content'].strip()
        rate = data['rate']

        if not content:
            return jsonify({"code": 400, "message": "评论内容不能为空"}), 400

        if rate not in range(1, 6):
            return jsonify({"code": 400, "message": "评分必须在1到5之间"}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 检查商品是否存在
            cursor.execute("SELECT id FROM spu WHERE id = ?", (spu_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "商品不存在"}), 404

            # 检查用户是否有订单状态为“已完成”的订单
            cursor.execute('''
                SELECT id FROM orders WHERE user_id = ? AND status = 4
            ''', (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 403, "message": "只有订单状态为已完成的用户才可以评论"}), 403

            # 插入评论
            cursor.execute('''
                SELECT avatar FROM users WHERE id = ?
            ''', (user_id,))
            avatar = cursor.fetchone()
            if not avatar:
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            cursor.execute('''
                INSERT INTO product_comment (spu_id, user_id, content, rate, touxiang, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (spu_id, user_id, content, rate, avatar[0], datetime.now()))
            conn.commit()

            return jsonify({"code": 200, "message": "评论成功"}), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


# 获取用户下的评论接口
# 获取用户下的评论接口
@app.route('/api/users/<int:user_id>/comments', methods=['GET'])
def get_user_comments(user_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 获取评论，包括用户的头像信息
            cursor.execute('''
                SELECT pc.id, pc.touxiang, pc.content, pc.rate, pc.is_anonymous, pc.created_at, pc.username, pc.spu_id
                FROM product_comment pc
                WHERE pc.user_id = ?
                ORDER BY pc.created_at DESC
            ''', (user_id,))
            comments = [dict(row) for row in cursor.fetchall()]

            # 构建最终的评论数据
            comments_data = []
            for comment in comments:
                comment_data = {
                    "id": comment['id'],
                    "content": comment['content'],
                    "rate": comment['rate'],
                    "is_anonymous": bool(comment['is_anonymous']),
                    "created_at": comment['created_at'],
                    "username": comment['username'],
                    "avatar": comment['touxiang'],
                    "spu_id": comment['spu_id']
                }

                # 获取 spu_id 的基本信息
                cursor.execute('''
                    SELECT spu.id, spu.name, spu.description, spu.main_image, spu.brand_id, spu.category_id
                    FROM spu
                    WHERE spu.id = ?
                ''', (comment['spu_id'],))
                spu_info = cursor.fetchone()
                if spu_info:
                    spu_data = {
                        "id": spu_info['id'],
                        "name": spu_info['name'],
                        "description": spu_info['description'],
                        "main_image": spu_info['main_image'],
                        "brand_id": spu_info['brand_id'],
                        "category_id": spu_info['category_id']
                    }
                    comment_data['spu'] = spu_data
                else:
                    comment_data['spu'] = None

                comments_data.append(comment_data)

            return jsonify({
                "code": 200,
                "data": {"items": comments_data},
                "message": "Success"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500








# 2. 获取没件商品的评论接口
@app.route('/api/products/<int:spu_id>/comments', methods=['GET'])
def get_product_comments(spu_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 检查商品是否存在
            cursor.execute("SELECT id FROM spu WHERE id = ?", (spu_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "商品不存在"}), 404

            # 获取评论，包括用户的头像信息
            cursor.execute('''
                SELECT pc.id, pc.touxiang,pc.content, pc.rate, pc.is_anonymous, pc.created_at, pc.username
                FROM product_comment pc
                WHERE pc.spu_id = ?
                ORDER BY pc.created_at DESC
            ''', (spu_id,))
            comments = [dict(row) for row in cursor.fetchall()]
            print(comments)

            # 构建最终的评论数据
            comments_data = []
            for comment in comments:
                comment_data = {
                    "id": comment['id'],
                    "content": comment['content'],
                    "rate": comment['rate'],
                    "is_anonymous": comment['is_anonymous'],
                    "created_at": comment['created_at'],
                    "username": comment['username'],
                    "avatar": comment['touxiang'],
                }
                comments_data.append(comment_data)

            return jsonify({
                "code": 200,
                "data": {"items": comments_data},
                "message": "Success"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

# 3. 更新评论接口（可选）
@app.route('/api/<int:user_id>/comments/<int:comment_id>', methods=['PUT'])
def update_product_comment(comment_id,user_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['content', 'rate']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        content = data['content'].strip()
        rate = data['rate']

        if not content:
            return jsonify({"code": 400, "message": "评论内容不能为空"}), 400

        if rate not in range(1, 6):
            return jsonify({"code": 400, "message": "评分必须在1到5之间"}), 400



        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 检查评论是否存在且属于当前用户
            cursor.execute("SELECT id FROM product_comment WHERE id = ? AND user_id = ?", (comment_id, user_id))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "评论不存在或不属于您"}), 404

            # 更新评论
            cursor.execute('''
                UPDATE product_comment
                SET content = ?, rate = ?, updated_at = ?
                WHERE id = ?
            ''', (content, rate, datetime.now(), comment_id))
            conn.commit()

            return jsonify({"code": 200, "message": "评论更新成功"}), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

# 4. 删除评论接口（可选）
@app.route('/api/comments/<int:comment_id>/<int:user_id>', methods=['DELETE'])
def delete_product_comment(comment_id,user_id):
    try:
        # 直接获取用户ID
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 检查评论是否存在且属于当前用户
            cursor.execute("SELECT id FROM product_comment WHERE id = ? AND user_id = ?", (comment_id, user_id))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "评论不存在或不属于您"}), 404

            # 删除评论
            cursor.execute("DELETE FROM product_comment WHERE id = ?", (comment_id,))
            conn.commit()

            return jsonify({"code": 200, "message": "评论删除成功"}), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

#购物车模块
# 1. 添加商品到购物车
@app.route('/api/cart/<int:user_id>', methods=['POST'])
def add_to_cart(user_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['sku_id', 'quantity']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        sku_id = data['sku_id']
        quantity = data['quantity']

        if not isinstance(sku_id, int) or not isinstance(quantity, int):
            return jsonify({"code": 400, "message": "字段类型错误"}), 400

        if quantity <= 0:
            return jsonify({"code": 400, "message": "数量必须大于0"}), 400

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 检查商品有效性
            cursor.execute("SELECT id, stock FROM sku WHERE id = ?", (sku_id,))
            sku = cursor.fetchone()
            if not sku:
                return jsonify({"code": 404, "message": "SKU不存在"}), 404

            # 检查SKU库存是否充足
            if sku[1] < quantity:
                return jsonify({"code": 400, "message": "库存不足"}), 400

            # 处理购物车逻辑
            cursor.execute("SELECT id, quantity FROM cart WHERE user_id = ? AND sku_id = ?",
                         (user_id, sku_id))
            cart_item = cursor.fetchone()

            if cart_item:
                new_quantity = cart_item['quantity'] + quantity
                cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?",
                             (new_quantity, cart_item['id']))
            else:
                cursor.execute("INSERT INTO cart (user_id, sku_id, quantity) VALUES (?, ?, ?)",
                             (user_id, sku_id, quantity))

            conn.commit()
            return jsonify({"code": 200, "message": "操作成功"}), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

# 3. 删除购物车商品（不依赖JWT）
@app.route('/api/cart/<int:user_id>/<int:item_id>', methods=['DELETE'])
def delete_from_cart(user_id, item_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证购物车项归属
            cursor.execute("SELECT id FROM cart WHERE id = ? AND user_id = ?",
                         (item_id, user_id))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "购物车项不存在"}), 404

            cursor.execute("DELETE FROM cart WHERE id = ?", (item_id,))
            conn.commit()
            return jsonify({"code": 200, "message": "删除成功"}), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


# 2. 获取购物车列表（不依赖JWT）
@app.route('/api/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 获取购物车数据
            cursor.execute('''
                SELECT c.id, c.sku_id, c.quantity, s.price, s.image, s.attributes AS sku_attributes,
                       spu.name AS spu_name, spu.id AS spu_id, spu.description AS spu_description, spu.main_image AS spu_main_image
                FROM cart c
                JOIN sku s ON c.sku_id = s.id
                JOIN spu ON s.spu_id = spu.id
                WHERE c.user_id = ?
            ''', (user_id,))

            cart_items = []
            for row in cursor.fetchall():
                item = dict(row)
                # 解析SKU属性
                sku_attributes = json.loads(item['sku_attributes'])
                item['sku_attributes'] = {attr['attribute_id']: attr['value'] for attr in sku_attributes}
                cart_items.append(item)

            return jsonify({
                "code": 200,
                "data": {"items": cart_items},
                "message": "Success"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


# 购物车更新接口
@app.route('/api/cart/<int:user_id>/<int:item_id>', methods=['PUT'])
def update_cart_item(user_id, item_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['quantity']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        quantity = data['quantity']

        # 验证数量有效性
        if not isinstance(quantity, int) or quantity < 1:
            return jsonify({"code": 400, "message": "数量必须为正整数"}), 400

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证购物车项归属
            cursor.execute("SELECT id, sku_id, quantity FROM cart WHERE id = ? AND user_id = ?",
                         (item_id, user_id))
            cart_item = cursor.fetchone()

            if not cart_item:
                return jsonify({"code": 404, "message": "购物车项不存在"}), 404

            # 获取SKU的库存
            sku_id = cart_item['sku_id']
            print(sku_id)
            cursor.execute("SELECT stock FROM sku WHERE id = ?", (sku_id,))
            sku_data = cursor.fetchone()


            if not sku_data:
                return jsonify({"code": 404, "message": "商品不存在"}), 404

            stock = sku_data['stock']
            print(stock)

            # 检查库存是否足够
            if quantity > stock:
                 return jsonify({"code": 400, "message": "库存不足"}), 400



            # 更新数量
            cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?",
                         (quantity, item_id))
            conn.commit()

            return jsonify({
                "code": 200,
                "message": "更新成功"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

# 实现勾选或取消勾选购物车中商品的功能
@app.route('/api/cart/<int:user_id>/<int:item_id>/select', methods=['PUT'])
def select_cart_item(user_id, item_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        selected = data.get('selected')
        if selected is None or not isinstance(selected, bool):
            return jsonify({"code": 400, "message": "缺少必要的selected字段或格式错误"}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证购物车项归属
            cursor.execute("SELECT id FROM cart WHERE id = ? AND user_id = ?", (item_id, user_id))
            cart_item = cursor.fetchone()

            if not cart_item:
                return jsonify({"code": 404, "message": "购物车项不存在"}), 404

            # 更新selected状态
            cursor.execute("UPDATE cart SET selected = ? WHERE id = ?", (selected, item_id))
            conn.commit()

            return jsonify({
                "code": 200,
                "message": "购物车项选择状态更新成功"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500



##订单模块
@app.route('/api/orders/<int:user_id>/<int:status>', methods=['GET'])
def get_user_orders_by_status(user_id, status):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 构建基础查询
            base_query = """
                SELECT o.*, 
                    spu.main_image as spu_main_image,
                    spu.description as spu_description
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                LEFT JOIN sku ON oi.sku_id = sku.id
                LEFT JOIN spu ON sku.spu_id = spu.id
                WHERE o.user_id = ?
            """
            params = [user_id]

            if 1 <= status <= 5:
                base_query += " AND o.status = ?"
                params.append(status)
            elif status != 0:  # 0表示全部状态
                return jsonify({"code": 400, "message": "无效的订单状态值"}), 400

            # 去重处理
            base_query += " GROUP BY o.id"
            cursor.execute(base_query, params)
            orders = cursor.fetchall()

            order_list = []
            for order in orders:
                order_dict = dict(order)
                order_id = order['id']

                # 获取订单商品明细（补充SPU/SKU信息）
                cursor.execute('''
                    SELECT oi.*, 
                        sku.attributes as sku_attributes,
                        spu.main_image as spu_main_image,
                        spu.description as spu_description
                    FROM order_items oi
                    JOIN sku ON oi.sku_id = sku.id
                    JOIN spu ON sku.spu_id = spu.id
                    WHERE oi.order_id = ?
                ''', (order_id,))
                items = []
                for item in cursor.fetchall():
                    item_data = dict(item)
                    # 解析SKU属性
                    attributes = json.loads(item_data['sku_attributes'])
                    item_data['specs'] = {attr['attribute_id']: attr['value'] for attr in attributes}
                    items.append(item_data)

                order_dict.update({
                    "spu_main_image": order['spu_main_image'],
                    "spu_description": order['spu_description'],
                    "items": items,
                    "address": get_related_data(cursor, 'order_address', order_id),
                    "payment": get_related_data(cursor, 'payment_records', order_id),
                    "logistics": get_related_data(cursor, 'order_logistics', order_id)
                })
                order_list.append(order_dict)

            return jsonify({
                "code": 200,
                "data": {
                    "total": len(order_list),
                    "orders": order_list
                },
                "message": "查询成功"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500
def get_related_data(cursor, table_name, order_id, is_list=False):
    """通用方法获取关联数据"""
    cursor.execute(f"SELECT * FROM {table_name} WHERE order_id = ?", (order_id,))
    result = cursor.fetchall()
    return [dict(row) for row in result] if is_list else (dict(result[0]) if result else None)



#获取当前用户的订单
# 获取用户订单接口
@app.route('/api/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 查询用户订单基础信息
            # 获取用户订单信息
            cursor.execute('''
                               SELECT 
                                   o.id, 
                                   o.order_no, 
                                   o.total_amount, 
                                   o.status, 
                                   strftime('%Y-%m-%dT%H:%M:%SZ', o.created_at) as created_at,
                                   strftime('%Y-%m-%dT%H:%M:%SZ', o.pay_time) as pay_time,
                                   strftime('%Y-%m-%dT%H:%M:%SZ', o.delivery_time) as delivery_time,
                                   strftime('%Y-%m-%dT%H:%M:%SZ', o.finish_time) as finish_time,
                                   ua.name as address_name,
                                   ua.phone as address_phone,
                                   ua.province as address_province,
                                   ua.city as address_city,
                                   ua.district as address_district,
                                   ua.detail as address_detail
                               FROM orders o
                               LEFT JOIN order_address oa ON o.id = oa.order_id
                               LEFT JOIN user_address ua ON oa.address_id = ua.id
                               WHERE o.user_id = ?
                           ''', (user_id,))

            orders = [dict(row) for row in cursor.fetchall()]

            # 查询每个订单的商品明细，并获取SPU的描述和图片以及规格属性
            for order in orders:
                cursor.execute('''
                    SELECT 
                        oi.sku_id,
                        oi.sku_name,
                        oi.sku_image,
                        oi.price,
                        oi.quantity,
                        s.attributes AS sku_attributes,
                        spu.description AS spu_description,
                        spu.main_image AS spu_main_image
                    FROM order_items oi
                    JOIN sku s ON oi.sku_id = s.id
                    JOIN spu ON s.spu_id = spu.id
                    WHERE oi.order_id = ?
                ''', (order['id'],))
                items = []
                for row in cursor.fetchall():
                    item = dict(row)
                    # 解析SKU属性
                    sku_attributes = json.loads(item['sku_attributes'])
                    item['sku_attributes'] = {attr['attribute_id']: attr['value'] for attr in sku_attributes}
                    items.append(item)
                order['items'] = items

            return jsonify({
                "code": 200,
                "data": {
                    "items": orders,
                    "total": len(orders)
                },
                "message": "Success"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库查询失败: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500








#获取用户的某一个订单详细信息
@app.route('/api/orders/<int:user_id>/<int:order_id>', methods=['GET'])
def get_order_details(user_id, order_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row  # 启用行转字典功能
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证订单归属
            cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
            order = cursor.fetchone()
            if not order:
                return jsonify({"code": 404, "message": "订单不存在或不属于您"}), 404

            # 获取订单地址信息
            cursor.execute("SELECT * FROM order_address WHERE order_id = ?", (order_id,))
            address = cursor.fetchone()

            # 获取订单商品明细
            cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
            items = cursor.fetchall()

            # 获取支付记录
            cursor.execute("SELECT * FROM payment_records WHERE order_id = ?", (order_id,))
            payment = cursor.fetchone()

            # 获取物流信息
            cursor.execute("SELECT * FROM order_logistics WHERE order_id = ?", (order_id,))
            logistics = cursor.fetchone()

            # 构建订单详细信息
            order_details = {
                "order_id": order['id'],
                "order_no": order['order_no'],
                "user_id": order['user_id'],
                "total_amount": order['total_amount'],
                "payment_method": order['payment_method'],
                "status": order['status'],
                "created_at": order['created_at'],
                "pay_time": order['pay_time'],
                "delivery_time": order['delivery_time'],
                "finish_time": order['finish_time'],
                "address": {
                    "id": address['id'],
                    "name": address['name'],
                    "phone": address['phone'],
                    "address": address['address']
                },
                "items": [
                    {
                        "id": item['id'],
                        "sku_id": item['sku_id'],
                        "sku_name": item['sku_name'],
                        "sku_image": item['sku_image'],
                        "price": item['price'],
                        "quantity": item['quantity']
                    }
                    for item in items
                ],
                "payment": {
                    "id": payment['id'],
                    "payment_no": payment['payment_no'],
                    "amount": payment['amount'],
                    "status": payment['status'],
                    "payment_time": payment['payment_time'],
                    "created_at": payment['created_at']
                } if payment else None,
                "logistics": {
                    "id": logistics['id'],
                    "logistics_no": logistics['logistics_no'],
                    "company_code": logistics['company_code'],
                    "company_name": logistics['company_name'],
                    "receiver_name": logistics['receiver_name'],
                    "receiver_phone": logistics['receiver_phone'],
                    "receiver_address": logistics['receiver_address'],
                    "created_at": logistics['created_at']
                } if logistics else None
            }

            return jsonify({
                "code": 200,
                "data": order_details,
                "message": "Success"
            }), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

#购物车提交生成订单
@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        user_id = data.get('user_id')
        cart_items = data.get('cart_items')
        address_id = data.get('address_id')
        new_address = data.get('new_address')

        if not user_id or not cart_items:
            return jsonify({"code": 400, "message": "缺少必要的字段"}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证购物车项
            cart_item_ids = [item['id'] for item in cart_items]
            cursor.execute('''
                SELECT c.id AS cart_id, c.sku_id, c.quantity, s.price
                FROM cart c
                JOIN sku s ON c.sku_id = s.id
                WHERE c.id IN ({})
                AND c.user_id = ?
            '''.format(','.join('?' for _ in cart_item_ids)), cart_item_ids + [user_id])
            fetched_cart_items = cursor.fetchall()

            if len(fetched_cart_items) != len(cart_items):
                return jsonify({"code": 400, "message": "购物车项无效"}), 400

            # 计算总金额
            total_amount = sum(item[3] * item[2] for item in fetched_cart_items)

            # 生成订单号
            order_no = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))

            # 创建订单主记录
            cursor.execute('''
                INSERT INTO orders 
                (order_no, user_id, total_amount, status, created_at)
                VALUES (?, ?, ?, 1, ?)
            ''', (order_no, user_id, total_amount, datetime.now()))
            order_id = cursor.lastrowid

            # 插入订单商品明细
            for item in fetched_cart_items:
                sku_id = item[1]
                quantity = item[2]
                price = item[3]

                cursor.execute('''
                    INSERT INTO order_items 
                    (order_id, sku_id, sku_name, sku_image, price, quantity)
                    SELECT ?, s.id, spu.name, spu.main_image, ?, ?
                    FROM sku s
                    JOIN spu ON s.spu_id = spu.id
                    WHERE s.id = ?
                ''', (order_id, price, quantity, sku_id))

            # 处理用户地址
            if address_id:
                # 验证地址是否存在且属于该用户
                cursor.execute('''
                    SELECT id FROM user_address WHERE id = ? AND user_id = ?
                ''', (address_id, user_id))
                if not cursor.fetchone():
                    return jsonify({"code": 400, "message": "地址无效"}), 400

                # 插入订单地址信息
                cursor.execute('''
                    INSERT INTO order_address 
                    (order_id, user_id, address_id)
                    VALUES (?, ?, ?)
                ''', (order_id, user_id, address_id))
            elif new_address:
                # 插入新地址
                name = new_address.get('name')
                phone = new_address.get('phone')
                province = new_address.get('province')
                city = new_address.get('city')
                district = new_address.get('district')
                detail = new_address.get('detail')
                is_default = new_address.get('is_default', False)

                cursor.execute('''
                    INSERT INTO user_address (
                        user_id, name, phone, province, 
                        city, district, detail, is_default, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    name,
                    phone,
                    province,
                    city,
                    district,
                    detail,
                    is_default,
                    datetime.now()
                ))

                # 获取新插入的地址ID
                address_id = cursor.lastrowid

                # 如果新地址设置为默认地址，更新其他地址为非默认
                if is_default:
                    cursor.execute('''
                        UPDATE user_address 
                        SET is_default = 0 
                        WHERE user_id = ? AND id != ?
                    ''', (user_id, address_id))

                # 插入订单地址信息
                cursor.execute('''
                    INSERT INTO order_address 
                    (order_id, user_id, address_id)
                    VALUES (?, ?, ?)
                ''', (order_id, user_id, address_id))
            else:
                return jsonify({"code": 400, "message": "缺少地址信息"}), 400

                # 删除购物车中的商品
            for cart_item in cart_items:
                    cursor.execute('''
                               DELETE FROM cart WHERE id = ? AND user_id = ?
                           ''', (cart_item['id'], user_id))

            conn.commit()

            return jsonify({
                "code": 200,
                "data": {
                    "order_id": order_id,
                    "order_no": order_no,
                    "total_amount": total_amount
                },
                "message": "订单创建成功"
            })

    except sqlite3.Error as e:
        conn.rollback()
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

#直接生成订单
@app.route('/api/orders/immediate', methods=['POST'])
def create_immediate_order():
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['user_id', 'spu_id', 'quantity', 'new_address']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        user_id = data['user_id']
        spu_id = data['spu_id']
        quantity = data['quantity']
        new_address = data['new_address']

        if not isinstance(quantity, int) or quantity < 1:
            return jsonify({"code": 400, "message": "数量必须为正整数"}), 400

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证商品有效性
            cursor.execute("SELECT id, stock FROM sku WHERE spu_id = ? LIMIT 1", (spu_id,))
            sku_data = cursor.fetchone()
            if not sku_data:
                return jsonify({"code": 404, "message": "商品不存在"}), 404

            sku_id = sku_data[0]
            stock = sku_data[1]

            # 检查库存是否足够
            if quantity > stock:
                return jsonify({"code": 400, "message": "库存不足"}), 400

            # 计算总金额（假设每个SKU的价格相同，实际应用中可能需要从SKU表中获取价格）
            cursor.execute("SELECT price FROM sku WHERE id = ?", (sku_id,))
            price = cursor.fetchone()[0]
            total_amount = quantity * price

            # 获取SPU的详细信息
            cursor.execute("""
                SELECT name, main_image 
                FROM spu 
                WHERE id = ?
            """, (spu_id,))
            spu_data = cursor.fetchone()
            if not spu_data:
                return jsonify({"code": 404, "message": "商品信息缺失"}), 404

            spu_name = spu_data[0]
            spu_image = spu_data[1]

            # 生成订单号
            order_no = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))

            # 创建订单主记录
            cursor.execute('''
                INSERT INTO orders 
                (order_no, user_id, total_amount, status, created_at)
                VALUES (?, ?, ?, 1, ?)
            ''', (order_no, user_id, total_amount, datetime.now()))

            order_id = cursor.lastrowid

            # 插入订单商品明细
            cursor.execute('''
                INSERT INTO order_items 
                (order_id, sku_id, sku_name, sku_image, price, quantity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, sku_id, spu_name, spu_image, price, quantity))

            # 处理用户地址
            if new_address:
                name = new_address.get('name').strip()
                phone = new_address.get('phone').strip()
                province = new_address.get('province').strip()
                city = new_address.get('city').strip()
                district = new_address.get('district').strip()
                detail = new_address.get('detail').strip()
                is_default = new_address.get('is_default', 0)  # 默认为0，即非默认地址

                # 插入新地址
                cursor.execute('''
                    INSERT INTO user_address (
                        user_id, name, phone, province, city, district, detail, is_default, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, name, phone, province, city, district, detail, is_default, datetime.now()))

                # 获取新插入的地址ID
                address_id = cursor.lastrowid

                # 如果新地址设置为默认地址，更新其他地址为非默认
                if is_default:
                    cursor.execute('''
                        UPDATE user_address 
                        SET is_default = 0 
                        WHERE user_id = ? AND id != ?
                    ''', (user_id, address_id))

                # 插入订单地址信息
                cursor.execute('''
                    INSERT INTO order_address 
                    (order_id, user_id, address_id)
                    VALUES (?, ?, ?)
                ''', (order_id, user_id, address_id))
            else:
                return jsonify({"code": 400, "message": "缺少地址信息"}), 400

            conn.commit()
            return jsonify({
                "code": 200,
                "data": {
                    "order_id": order_id,
                    "order_no": order_no,
                    "total_amount": total_amount
                },
                "message": "订单创建成功"
            })

    except sqlite3.Error as e:
        conn.rollback()
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500






# 删除某个用户的订单
@app.route('/api/orders/<int:user_id>/<int:order_id>', methods=['DELETE'])
def delete_order(user_id, order_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证订单归属
            cursor.execute("SELECT id FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "订单不存在或不属于您"}), 404

            # 删除订单项
            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))

            # 删除订单记录
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))

            conn.commit()
            return jsonify({"code": 200, "message": "订单删除成功"}), 200

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

# 用户只能修改未支付的订单
@app.route('/api/orders/<int:user_id>/<int:order_id>', methods=['PUT'])
def update_order(user_id, order_id):
    """
    更新订单接口
    请求参数：
    {
        "quantity": 2,  // 必须（正整数）
        "address": {  // 可选地址信息
            "address_id": 1,  // 使用现有地址时提供
            // 或提供新地址信息
            "new_address": {
                "name": "张三",
                "phone": "13800138000",
                "province": "广东省",
                "city": "深圳市",
                "district": "南山区",
                "detail": "科技园路123号",
                "is_default": true
            }
        }
    }
    """
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        # 参数校验
        new_quantity = data.get('quantity')
        address_info = data.get('address', {})

        # 校验数量有效性
        if not isinstance(new_quantity, int) or new_quantity <= 0:
            return jsonify({"code": 400, "message": "商品数量必须为正整数"}), 400

        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 验证订单有效性
            cursor.execute('''
                SELECT o.id, o.status, o.total_amount 
                FROM orders o 
                WHERE o.id = ? AND o.user_id = ?
            ''', (order_id, user_id))
            order = cursor.fetchone()
            if not order:
                return jsonify({"code": 404, "message": "订单不存在或不属于您"}), 404

            if order['status'] != 1:
                return jsonify({"code": 403, "message": "只能修改待付款订单"}), 403

            # 事务开始
            conn.execute("BEGIN TRANSACTION")

            try:
                # 获取订单项和SKU信息
                cursor.execute('''
                    SELECT oi.id AS order_item_id, oi.quantity AS old_quantity, 
                           oi.sku_id, s.price, s.stock
                    FROM order_items oi
                    JOIN sku s ON oi.sku_id = s.id
                    WHERE oi.order_id = ?
                ''', (order_id,))
                order_items = cursor.fetchall()

                if not order_items:
                    raise ValueError("订单中没有商品项")

                total_amount = 0
                for order_item in order_items:
                    sku_id = order_item['sku_id']
                    old_quantity = order_item['old_quantity']

                    # 计算库存变化
                    stock_change = new_quantity - old_quantity

                    # 校验库存
                    if stock_change > 0:  # 仅校验增加数量的情况
                        if order_item['stock'] < stock_change:
                            raise ValueError(f"商品库存不足，SKU ID: {sku_id}")

                    # 更新订单项数量
                    cursor.execute('''
                        UPDATE order_items 
                        SET quantity = ?
                        WHERE id = ?
                    ''', (new_quantity, order_item['order_item_id']))

                    # 累计总金额
                    total_amount += order_item['price'] * new_quantity

                # 更新订单总金额
                cursor.execute('''
                    UPDATE orders 
                    SET total_amount = ?
                    WHERE id = ?
                ''', (total_amount, order_id))

                # 处理地址信息
                if address_info:
                    if 'address_id' in address_info:
                        # 验证现有地址归属
                        cursor.execute('''
                            SELECT id 
                            FROM user_address 
                            WHERE id = ? AND user_id = ?
                        ''', (address_info['address_id'], user_id))
                        if not cursor.fetchone():
                            raise ValueError("地址信息不存在或不属于您")

                        # 更新订单地址关联
                        cursor.execute('''
                            UPDATE order_address 
                            SET address_id = ? 
                            WHERE order_id = ?
                        ''', (address_info['address_id'], order_id))
                    elif 'new_address' in address_info:
                        # 插入新地址逻辑
                        addr = address_info['new_address']
                        name = addr.get('name').strip()
                        phone = addr.get('phone').strip()
                        province = addr.get('province').strip()
                        city = addr.get('city').strip()
                        district = addr.get('district').strip()
                        detail = addr.get('detail').strip()
                        is_default = addr.get('is_default', 0)  # 默认为0，即非默认地址

                        # 校验地址信息
                        if not all([name, phone, province, city, district, detail]):
                            raise ValueError("新地址信息不完整")

                        # 插入新地址
                        cursor.execute('''
                            INSERT INTO user_address (
                                user_id, name, phone, province, city, district, detail, is_default, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (user_id, name, phone, province, city, district, detail, is_default, datetime.now()))

                        # 获取新插入的地址ID
                        address_id = cursor.lastrowid

                        # 如果新地址设置为默认地址，更新其他地址为非默认
                        if is_default:
                            cursor.execute('''
                                UPDATE user_address 
                                SET is_default = 0 
                                WHERE user_id = ? AND id != ?
                            ''', (user_id, address_id))

                        # 更新订单地址关联
                        cursor.execute('''
                            UPDATE order_address 
                            SET address_id = ? 
                            WHERE order_id = ?
                        ''', (address_id, order_id))

                conn.commit()
                return jsonify({
                    "code": 200,
                    "data": {
                        "order_id": order_id,
                        "new_total": total_amount
                    },
                    "message": "订单更新成功"
                })

            except ValueError as ve:
                conn.rollback()
                return jsonify({"code": 400, "message": str(ve)}), 400
            except Exception as e:
                conn.rollback()
                app.logger.error(f"系统异常: {str(e)}")
                return jsonify({"code": 500, "message": "服务器内部错误"}), 500

    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500






# 模拟支付完成后更新订单状态为已支付

scheduler = BackgroundScheduler()
scheduler.start()
#模拟订单状态为已支付在五分钟后更新订单状态为已发货
def update_order_status_to_shipped(order_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 更新订单状态为已发货，并记录发货时间
            cursor.execute("UPDATE orders SET status = 3, delivery_time = ? WHERE id = ?", (datetime.now(), order_id))

            conn.commit()
            app.logger.info(f"订单 {order_id} 状态已更新为已发货")
    except sqlite3.Error as e:
        app.logger.error(f"数据库错误: {str(e)}")
    except Exception as e:
        app.logger.error(f"系统异常: {str(e)}")

@app.route('/api/orders/<int:user_id>/<int:order_id>/pay', methods=['POST'])
def pay_order(user_id, order_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"code": 400, "message": "请求格式错误"}), 400

        required_fields = ['receiver_name', 'receiver_phone', 'receiver_address']
        if any(field not in data for field in required_fields):
            return jsonify({"code": 400, "message": "缺少必要字段"}), 400

        receiver_name = data['receiver_name'].strip()
        receiver_phone = data['receiver_phone'].strip()
        receiver_address = data['receiver_address'].strip()

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证订单归属
            cursor.execute("SELECT id, status, total_amount FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
            order = cursor.fetchone()
            if not order:
                return jsonify({"code": 404, "message": "订单不存在或不属于您"}), 404

            # 验证订单状态是否为待付款
            if order[1] != 1:
                return jsonify({"code": 403, "message": "订单状态不是待付款"}), 403

            # 生成支付编号
            payment_no = generate_verification_code()

            # 更新订单状态为已付款，并记录支付时间和支付方式
            cursor.execute("UPDATE orders SET status = 2, pay_time = ?, payment_method = 1 WHERE id = ?", (datetime.now(), order_id))

            # 插入支付记录
            cursor.execute('''
                INSERT INTO payment_records (order_id, payment_no, amount, status, payment_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, payment_no, order[2], 1, datetime.now()))

            # 插入物流信息
            logistics_no = generate_verification_code()
            cursor.execute('''
                INSERT INTO order_logistics (order_id, logistics_no, company_code, company_name, receiver_name, receiver_phone, receiver_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, logistics_no, 'WX', '微信物流', receiver_name, receiver_phone, receiver_address))

            conn.commit()

            # 添加定时任务，五分钟后更新订单状态为已发货
            scheduler.add_job(update_order_status_to_shipped,
                              'date', run_date=datetime.now() + timedelta(minutes=5),
                              args=[order_id])

            return jsonify({
                "code": 200,
                "data": {
                    "order_id": order_id,
                    "status": 2,
                    "payment_no": payment_no,
                    "logistics_no": logistics_no
                },
                "message": "订单支付成功"
            }), 200

    except sqlite3.Error as e:
        conn.rollback()
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


# 催发货接口
@app.route('/api/orders/<int:user_id>/<int:order_id>/ship', methods=['POST'])
def ship_order(user_id, order_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证订单归属
            cursor.execute("SELECT id, status FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
            order = cursor.fetchone()

            if not order:
                return jsonify({"code": 404, "message": "订单不存在或不属于您"}), 404

            # 验证订单状态是否为已付款
            if order[1] != 2:
                return jsonify({"code": 403, "message": "只有已付款的订单才可以催发货"}), 403

            # 更新订单状态为已发货
            cursor.execute("UPDATE orders SET status = 3 WHERE id = ?", (order_id,))


            conn.commit()

            return jsonify({
                "code": 200,
                "message": "订单已发货"
            })

    except sqlite3.Error as e:
        conn.rollback()
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


#确认收货的接口
@app.route('/api/orders/<int:user_id>/<int:order_id>/receive', methods=['POST'])
def receive_order(user_id, order_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # 验证用户有效性
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({"code": 404, "message": "用户不存在"}), 404

            # 验证订单归属
            cursor.execute("SELECT id, status FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
            order = cursor.fetchone()
            if not order:
                return jsonify({"code": 404, "message": "订单不存在或不属于您"}), 404

            # 验证订单状态是否为已发货
            if order[1] != 3:
                return jsonify({"code": 403, "message": "只有已发货的订单才可以确认收货"}), 403

            # 更新订单状态为已完成，并记录完成时间
            cursor.execute("UPDATE orders SET status = 4, finish_time = ? WHERE id = ?", (datetime.now(), order_id))

            conn.commit()

            return jsonify({
                "code": 200,
                "message": "订单已确认收货"
            }), 200

    except sqlite3.Error as e:
        conn.rollback()
        app.logger.error(f"数据库错误: {str(e)}")
        return jsonify({"code": 500, "message": "数据库操作失败"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"系统异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

# 支付接口

if __name__ == '__main__':
    app.run(debug=True)



























