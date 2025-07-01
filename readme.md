# 🚀 校园失物招领平台 | Campus Lost & Found 

​	一个集 **智能匹配、地图定位、实时通知** 于一体的现代化校园失物招领解决方案。我们的目标不仅是高效地帮助物品找到主人，更是通过技术在校园内传递一份温暖与互助。

---

## ✨ 核心功能 (Key Features)

- **👤 用户系统**: 提供安全的用户注册、登录与会话管理。
- **📢 信息发布**: 支持发布失物/拾物信息，包含详细描述、时间、地点，并可上传物品图片。
- **🗺️ 地图集成**: 用户可在校园地图上精确标记物品位置，并支持按地理区域筛选信息。
- **🔍 智能搜索**: 提供基于关键词、分类、日期的多维度模糊搜索。
- **🤖 智能匹配与推送**: 新信息发布后，系统自动进行匹配，并通过邮件主动推送给相关用户。
- **💬 站内私信**: 用户可就特定物品进行一对一私信沟通，保护个人隐私。
- **📧 即时邮件提醒**: 当收到新私信或有物品匹配时，系统自动发送邮件通知。
- **🏠 个人中心**: 用户可以集中管理自己发布的所有信息，包括编辑、删除和更新物品状态。

---

## 🌟 技术亮点 (Technical Highlights)

- **智能匹配算法**: 后端采用 `Jieba` 分词库对物品名称和描述进行中文分词处理，结合地点、时间窗口等多维信息，构建高效的模糊匹配查询。
- **动态地图坐标转换**: 前端通过 JavaScript 实时计算用户点击位置在不同分辨率下的相对坐标，确保地图标记在任何设备上都能精准显示和存储 。
- **异步邮件通知**: 邮件发送任务通过独立的线程执行 (`send_async_email`)，避免了因网络延迟阻塞主应用进程，保证了流畅的用户体验。
- **RESTful 风格接口**: 提供了一套清晰、规范的后端路由，便于未来进行功能扩展。

---

## 🛠️ 安装与运行 (Installation & Setup)

#### 1. 环境依赖

- **Python 3.8+**
- **MySQL Server**

在开始前，请确保你的系统已安装 **Python 3.8+**、**pip** 和 **MySQL 服务器**。

#### 2. 安装步骤

1. **克隆代码**:
   
   若电脑安装有Git软件则命令行运行下面命令：
   ```bash
   git clone https://github.com/YuanShenT/Campus-Lost-Found-System.git
   cd Campus-Lost-Found-System
   ```
   若没有，也可选择通过浏览器到 https://github.com/YuanShenT/Campus-Lost-Found-System 下载项目压缩包。
   
2. **创建并激活虚拟环境**:

   强烈建议使用虚拟环境来管理项目依赖。

   ```bash
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   # macOS/Linux:
   source venv/bin/activate
   # Windows (Command Prompt):
   venv\Scripts\activate.bat
   # Windows (PowerShell):
   venv\Scripts\Activate.ps1
   ```

3. **安装依赖**:


   ```bash
   pip install -r requirements.txt
   ```
   
4. **配置数据库**:

   本项目使用 MySQL 数据库。请按照以下步骤进行设置：

   1. **启动你的 MySQL 服务器。**

   2. **创建数据库和表：**
      连接到你的 MySQL 服务器（例如，通过命令行输入 `mysql -u root -p` 并输入密码），然后执行以下 SQL 命令来创建 `lost_and_found` 数据库和所需的表结构：

      ```sql
      -- 创建数据库
      CREATE DATABASE IF NOT EXISTS lost_and_found CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
      
      -- 连接到数据库
      USE lost_and_found;
      
      -- 创建 users 表
      CREATE TABLE `users` (
        `id` int NOT NULL AUTO_INCREMENT,
        `username` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
        `email` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
        `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
        PRIMARY KEY (`id`),
        UNIQUE KEY `username` (`username`),
        UNIQUE KEY `email` (`email`)
      ) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
      
      -- 创建 items 表
      CREATE TABLE `items` (
        `id` int NOT NULL AUTO_INCREMENT,
        `type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
        `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
        `description` text COLLATE utf8mb4_unicode_ci,
        `location` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
        `event_time` datetime NOT NULL,
        `image_file` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT 'default.jpg',
        `user_id` int NOT NULL,
        `posted_date` datetime NOT NULL,
        `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
        `pin_x` int DEFAULT NULL,
        `pin_y` int DEFAULT NULL,
        PRIMARY KEY (`id`),
        KEY `idx_items_user_id` (`user_id`),
        CONSTRAINT `fk_items_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
        CONSTRAINT `items_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
      ) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
      
      -- 创建 messages 表
      CREATE TABLE `messages` (
        `id` int NOT NULL AUTO_INCREMENT,
        `sender_id` int NOT NULL,
        `receiver_id` int NOT NULL,
        `item_id` int DEFAULT NULL,
        `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
        `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `is_read` tinyint(1) NOT NULL DEFAULT '0',
        PRIMARY KEY (`id`),
        KEY `sender_id` (`sender_id`),
        KEY `receiver_id` (`receiver_id`),
        KEY `item_id` (`item_id`),
        CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`),
        CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`),
        CONSTRAINT `messages_ibfk_3` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`)
      ) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
      ```

   - **配置 `config.py`：**
     打开项目根目录下的 `config.py` 文件。
     将 `SQLALCHEMY_DATABASE_URI` 中的 `root:password@localhost` 替换为你的 MySQL 数据库的**实际用户名和密码**（例如 `your_mysql_username:your_mysql_password@your_mysql_host`）。同时，你也可以考虑将 `SECRET_KEY` 替换为一个固定且更安全的字符串。

     ```python
     # config.py
     import os
     
     class Config:
         # SECRET_KEY 用于 Flask 会话、CSRF 保护等。
         # 生产环境建议从环境变量获取，例如 os.environ.get('SECRET_KEY')
         SECRET_KEY = os.urandom(24).hex() # <-- **请修改为一个固定且安全的字符串！**
     
         # MySQL 数据库连接 URI： 'mysql+pymysql://用户名:密码@主机/数据库名'
         SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/lost_and_found' # <-- **请替换为你的实际数据库凭据！**
         SQLALCHEMY_TRACK_MODIFICATIONS = False
     
         # 图片上传目录，确保 static/uploads 目录存在且有写入权限
         UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')
         MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 最大文件上传大小 16 MB
     ```


5. **邮件服务器配置**:
      务必将以下占位符替换为你实际的邮件服务提供商信息。 例如，如果你使用 Gmail，可能需要开启“两步验证”并生成“应用专用密码”。如果你使用 QQ 邮箱，则需要使用“授权码”。

      ```python
      # apps.py
      MAIL_USERNAME = 'your_email@example.com' # 你的发件邮箱地址
      MAIL_PASSWORD = 'your_email_app_password_or_auth_code'  # 你的邮箱应用专用密码或授权码
      MAIL_DEFAULT_SENDER = 'your_email@example.com' # 默认发件人
      ```

#### 3. 运行程序

   在项目根目录下，确保虚拟环境已激活，然后执行：

   ```bash
   python app.py
   ```

   应用程序将会在**http://127.0.0.1:5000/** 运行。在浏览器中打开此地址即可开始使用。


---

## ⚙️ 核心功能实现深度解析 (In-depth Analysis)

#### 1.地图集成与坐标处理 

- **前端实现**: 在发布 (`publish_item.html`) 和编辑 (`edit_item.html`) 页面，JavaScript 监听对地图图片的点击事件 4。它会获取点击位置相对于图片左上角的

  **显示坐标**。为了适应不同屏幕尺寸下的图片缩放，脚本会根据图片的**原始尺寸** (1887x1183像素) 和**当前显示尺寸**计算出缩放比例。最终，将点击的显示坐标按比例换算回**原始图片坐标**，并存入隐藏的表单字段 (`pin_x`, `pin_y`) 中提交给后端 7。

- **后端实现**: `publish_item` 和 `edit_item` 路由在 `app.py` 中接收这些坐标，并将其作为整数存入 `Item` 模型。在物品详情页 (`item_detail.html`)，后端将原始坐标和原始地图尺寸传递给模板。前端 JavaScript 再次进行等比缩放，计算出图钉在当前用户屏幕上应有的正确位置并显示。

#### 2. 智能匹配与邮件推送

该功能在 `app.py` 的 `find_matching_items` 函数中实现。

- **触发时机**: 当一个新物品在 `publish_item` 路由中成功保存后立即触发。
- **匹配逻辑**:
  1. **类型反转**: 若发布的是“失物”，则在“拾物”中搜索，反之亦然。
  2. **关键词提取**: 使用 `jieba.cut_for_search` 对新物品的名称和描述进行中文分词，并过滤掉常见的停用词，生成关键词列表。
  3. **多维度匹配**:
     - **关键词匹配**: 使用 `SQLAlchemy` 的 `or_` 和 `like` 查询，在目标类型的物品中寻找名称或描述包含任何一个关键词的记录。
     - **地点匹配**: 同时对地点文字描述也进行分词和模糊匹配。
     - **时间窗口**: 只匹配 `event_time` (事件发生时间) 在正负7天内的物品。
- **邮件推送**: 如果找到匹配项，系统会调用 `send_email_notification` 函数，使用 `email_match_notification.html` 模板，生成一封包含双方物品详细信息的邮件，并分别发送给两位发布者。

#### 3. 站内私信与即时提醒

- **后端模型**: `Message` 模型在 `models.py` 中定义，通过外键同时关联发送者、接收者和相关的物品 。
- **发送逻辑**: 用户在物品详情页 (`item_detail.html`) 点击“联系发布者”按钮，会跳转到 `send_message` 路由。消息成功保存后，立即调用 `send_email_notification` 函数，使用 `email_new_message.html` 模板向接收者发送新消息邮件提醒。
- **消息查看**: `my_messages` 页面会查询所有与当前用户相关的消息，并按时间倒序排列。访问该页面时，所有未读消息会自动标记为已读。

---

## 🔌 API 路由参考 (API Endpoints)

| 路由 (Route)                        | HTTP 方法     | 功能描述                   | 需要登录    |
| ----------------------------------- | ------------- | -------------------------- | ----------- |
| `/`                                 | `GET`         | 首页，显示信息墙和搜索功能 | 否          |
| `/register`                         | `GET`, `POST` | 用户注册                   | 否          |
| `/login`                            | `GET`, `POST` | 用户登录                   | 否          |
| `/logout`                           | `GET`         | 用户登出                   | 是          |
| `/publish`                          | `GET`, `POST` | 发布新的失物/拾物信息      | 是          |
| `/item/<int:item_id>`               | `GET`         | 查看单个物品的详细信息     | 否          |
| `/edit_item/<int:item_id>`          | `GET`, `POST` | 编辑已发布的物品信息       | 是 (所有者) |
| `/item/<int:item_id>/delete`        | `POST`        | 删除物品信息               | 是 (所有者) |
| `/item/<int:item_id>/mark_resolved` | `POST`        | 将物品标记为“已解决”       | 是 (所有者) |
| `/dashboard`                        | `GET`         | 用户个人中心               | 是          |
| `/messages`                         | `GET`         | 查看我的消息列表           | 是          |
| `/message/send/<int:receiver_id>`   | `GET`, `POST` | 发送私信                   | 是          |

---

## 📂 项目结构 (Project Structure)

```structured text
/
├── app.py              # Flask 应用主文件，包含所有路由和核心逻辑
├── models.py           # 数据库模型定义 (SQLAlchemy)
├── config.py           # 应用程序配置 (数据库URI, SECRET_KEY)
├── requirements.txt    # 项目依赖列表
├── static/
│   ├── css/
│   │   └── style.css   # 全局CSS样式
│   ├── images/
│   │   └── pin.png     # 地图图钉图标
│   ├── map/
│   │   └── map.png     # 校园地图图片
│   └── uploads/        # 用户上传的物品图片
├── templates/
│   ├── index.html              # 首页 & 信息墙
│   ├── login.html              # 登录页
│   ├── register.html           # 注册页
│   ├── publish_item.html       # 发布信息页
│   ├── item_detail.html        # 物品详情页
│   ├── user_dashboard.html     # 个人中心
│   ├── edit_item.html          # 编辑信息页
│   ├── my_messages.html        # 我的消息页
│   ├── send_message.html       # 发送消息页
│   └── emails/                 # 邮件模板目录
│       ├── email_match_notification.html
│       └── email_new_message.html
└── README.md           # 本文件
```

---

## 🏗️ 系统架构 (Architecture)

```mermaid
graph TD
    subgraph "Browser"
        A["用户界面-(HTML/CSS/JS)"]
    end

    subgraph "Server (Flask Application)"
        B["路由与视图 (app.py)"]
        C["业务逻辑 (智能匹配/通知)"]
        D["ORM模型 (models.py)"]
    end

    subgraph "Infrastructure"
        E["MySQL数据库"]
        F["SMTP邮件服务器"]
        G["文件存储 (上传的图片)"]
    end

    A -- HTTP请求 --> B
    B -- 调用 --> C
    C -- 读/写 --> D
    D -- 数据库交互 --> E
    C -- 发送请求 --> F
    B -- 读/写文件 --> G
```

---

## 🛠️ 技术栈 (Technology Stack)

| 类别         | 技术                                                         |
| ------------ | ------------------------------------------------------------ |
| **后端**     | Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, Flask-Mail, Werkzeug |
| **数据库**   | MySQL, PyMySQL (驱动)                                        |
| **核心工具** | Jieba (中文分词)                                             |
| **前端**     | HTML5, CSS3, JavaScript (原生)                               |

---

## 🌍 生产环境部署 (Deployment)

​	开发环境中的 `app.run(debug=True)` 不适用于生产。在生产环境中，推荐使用生产级的 WSGI 服务器，例如 Gunicorn。

**使用 Gunicorn 部署示例:**

```bash
# 安装 Gunicorn
pip install gunicorn

# 运行应用 (假设主文件为 app.py, 应用实例为 app)
gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
```

---

## 🤝 如何贡献 (Contributing)

我们欢迎任何形式的贡献！

1. **Fork** 本仓库。
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)。
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4. 将您的分支推送到远程仓库 (`git push origin feature/AmazingFeature`)。
5. 开启一个 Pull Request。

---

## 📜 许可证 (License)

​	本项目基于 [MIT License](https://www.google.com/search?q=LICENSE.txt) 开源 。你可以自由使用、修改和分发本代码，但需保留原始版权声明。详情请参见项目根目录下的 `LICENSE` 文件。

