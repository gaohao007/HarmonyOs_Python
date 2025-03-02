# 配置数据库
import sqlite3

DATABASE = 'database.db'


def init_db():
    # 链接数据库db = SQLite3
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
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
                          ('季节', 1)
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
                            (1, '黑色'), (1, '白色'), (1, '藏青'), (1, '米色'),(1,'中灰'),
                            (2, 'S'), (2, 'M'), (2, 'L'), (2, 'XL'), (2, 'XXL'), (2, 'XXXL'),(2, 'XXXXL'),(2,'48'),(2,'50'),(2,'52'),(2,'54'),(2,'56'),(2,'60')
                            (3, '纯棉'), (3, '涤纶'), (3, '混纺'),
                            (4, '春季'), (4, '夏季'), (4, '秋季'), (4, '冬季')
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
                                    ('ZHR则则','static/images/BrandLogo/ZHR则则/logo.png','ZHR是一家注重脚感和细节的有态度的品牌：品牌专注于女鞋，通过充满时尚感的设计、高舒适度的穿着体验、符合人体工学的设计原理，为顾客呈现高性价比的优质产品。','static/images/BrandLogo/ZHR则则/back.jpg');
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
                          '["static/images/nanzhuang/man_2_1.jpg","static/images/nanzhuang/man_2_2.jpg","static/images/nanzhuang/man_2_3.jpg","static/images/nanzhuang/man_2_4.jpg","static/images/nanzhuang/man_2_5.jpg"]', 1),
                          
                          (1, 4, '刺绣男式卫衣', '春季时尚休闲舒适亲肤经典狼标刺绣男式卫衣', 
                          'static/images/nanzhuang/man_4_1.jpg',
                          '["static/images/nanzhuang/man_4_1.jpg","static/images/nanzhuang/man_4_2.jpg","static/images/nanzhuang/man_4_3.jpg","static/images/nanzhuang/man_4_4.jpg","static/images/nanzhuang/man_4_5.jpg","static/images/nanzhuang/man_4_6.jpg","static/images/nanzhuang/man_4_7.jpg","static/images/nanzhuang/man_4_8.jpg"]', 1),

                      ''')

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
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),
                           
                           
                               --刺绣男式卫衣

                            (3, 107.00, 4, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"52"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),

                           (3, 107.00, 12, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"54"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),

                           (3, 107.00, 0, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"56"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),

                           (3, 107.00, 3, 
                           '[{"attribute_id":1, "value":"黑色"}, {"attribute_id":2, "value":"60"}]',
                           '["static/images/nanzhuang/man_2_3_1.jpg","static/images/nanzhuang/man_2_3_2.jpg","static/images/nanzhuang/man_2_3_3.jpg","static/images/nanzhuang/man_2_3_4.jpg","static/images/nanzhuang/man_2_3_5.jpg","static/images/nanzhuang/man_2_3_6.jpg"]'),

                         
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



