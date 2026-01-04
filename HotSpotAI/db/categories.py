"""
分类 (categories) 数据库操作模块
"""
from typing import List, Dict, Optional
from core.db_pool import get_db
from core.config import add_log


# 预定义分类数据
DEFAULT_CATEGORIES = [
    {
        "name": "AI科技",
        "slug": "ai-tech",
        "description": "人工智能、前沿科技",
        "icon": "🤖",
        "color": "#6366f1",
        "keywords": ["AI", "ChatGPT", "人工智能", "大模型", "芯片", "半导体", "5G", "区块链"]
    },
    {
        "name": "财经投资",
        "slug": "finance",
        "description": "金融、投资、股市",
        "icon": "💰",
        "color": "#10b981",
        "keywords": ["股票", "基金", "理财", "A股", "港股", "美股", "比特币", "金融"]
    },
    {
        "name": "职场成长",
        "slug": "career",
        "description": "职业发展、技能提升",
        "icon": "💼",
        "color": "#f59e0b",
        "keywords": ["职场", "面试", "薪资", "裁员", "跳槽", "考证", "副业", "创业"]
    },
    {
        "name": "健康养生",
        "slug": "health",
        "description": "健康、医疗、养生",
        "icon": "🏥",
        "color": "#ef4444",
        "keywords": ["健康", "医疗", "养生", "减肥", "健身", "疫苗", "医保", "疫情"]
    },
    {
        "name": "教育育儿",
        "slug": "education",
        "description": "教育、育儿、学习",
        "icon": "📚",
        "color": "#8b5cf6",
        "keywords": ["教育", "高考", "考研", "留学", "育儿", "双减", "培训", "幼升小"]
    },
    {
        "name": "数码评测",
        "slug": "digital",
        "description": "数码产品、评测",
        "icon": "📱",
        "color": "#3b82f6",
        "keywords": ["手机", "电脑", "平板", "耳机", "相机", "测评", "发布会", "新品"]
    },
    {
        "name": "美食生活",
        "slug": "food",
        "description": "美食、生活方式",
        "icon": "🍜",
        "color": "#f97316",
        "keywords": ["美食", "菜谱", "餐厅", "探店", "外卖", "咖啡", "奶茶", "零食"]
    },
    {
        "name": "影视娱乐",
        "slug": "entertainment",
        "description": "影视、综艺、娱乐",
        "icon": "🎬",
        "color": "#ec4899",
        "keywords": ["电影", "电视剧", "综艺", "明星", "娱乐圈", "票房", "剧集", "档期"]
    },
    {
        "name": "旅游出行",
        "slug": "travel",
        "description": "旅游、交通、出行",
        "icon": "✈️",
        "color": "#06b6d4",
        "keywords": ["旅游", "机票", "酒店", "景点", "自驾", "假期", "交通", "出行"]
    },
    {
        "name": "情感心理",
        "slug": "emotion",
        "description": "情感、心理、人际关系",
        "icon": "💕",
        "color": "#d946ef",
        "keywords": ["恋爱", "婚姻", "情感", "心理", "抑郁", "焦虑", "社交", "人际关系"]
    }
]


async def get_categories(include_inactive: bool = False) -> List[Dict]:
    """
    获取所有分类

    Args:
        include_inactive: 是否包含未激活的分类

    Returns:
        分类列表
    """
    categories = []
    try:
        async with get_db() as db:
            where_clause = "" if include_inactive else "WHERE is_active = 1"

            async with db.execute(f'''
                SELECT id, name, slug, description, icon, color, is_active, sort_order, created_at, updated_at
                FROM categories
                {where_clause}
                ORDER BY sort_order ASC, id ASC
            ''') as cursor:
                rows = await cursor.fetchall()

            for r in rows:
                categories.append({
                    "id": r['id'],
                    "name": r['name'],
                    "slug": r['slug'],
                    "description": r['description'],
                    "icon": r['icon'],
                    "color": r['color'],
                    "is_active": bool(r['is_active']),
                    "sort_order": r['sort_order'],
                    "created_at": r['created_at'],
                    "updated_at": r['updated_at']
                })

    except Exception as e:
        add_log('error', f'获取分类列表失败: {e}')

    return categories


async def get_category_by_id(category_id: int) -> Optional[Dict]:
    """
    获取分类详情（含关键词和平台配置）

    Args:
        category_id: 分类ID

    Returns:
        分类详情，包含关键词列表和平台配置
    """
    try:
        async with get_db() as db:
            # 获取分类基本信息
            async with db.execute('''
                SELECT id, name, slug, description, icon, color, is_active, sort_order, created_at, updated_at
                FROM categories
                WHERE id = ?
            ''', (category_id,)) as cursor:
                row = await cursor.fetchone()

            if not row:
                return None

            category = {
                "id": row['id'],
                "name": row['name'],
                "slug": row['slug'],
                "description": row['description'],
                "icon": row['icon'],
                "color": row['color'],
                "is_active": bool(row['is_active']),
                "sort_order": row['sort_order'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at'],
                "keywords": [],
                "platforms": []
            }

            # 获取关键词
            async with db.execute('''
                SELECT keyword, weight
                FROM category_keywords
                WHERE category_id = ?
                ORDER BY weight DESC, id ASC
            ''', (category_id,)) as cursor:
                keyword_rows = await cursor.fetchall()
                for kr in keyword_rows:
                    category["keywords"].append({
                        "keyword": kr['keyword'],
                        "weight": kr['weight']
                    })

            # 获取平台配置
            async with db.execute('''
                SELECT platform, is_enabled
                FROM category_platforms
                WHERE category_id = ?
            ''', (category_id,)) as cursor:
                platform_rows = await cursor.fetchall()
                for pr in platform_rows:
                    category["platforms"].append({
                        "platform": pr['platform'],
                        "is_enabled": bool(pr['is_enabled'])
                    })

            return category

    except Exception as e:
        add_log('error', f'获取分类详情失败: {e}')
        return None


async def get_categories_with_keywords() -> List[Dict]:
    """
    获取所有分类及其关键词（用于抓取任务）

    Returns:
        分类列表，每个分类包含关键词
    """
    categories = []
    try:
        async with get_db() as db:
            async with db.execute('''
                SELECT id, name, slug, is_active
                FROM categories
                WHERE is_active = 1
                ORDER BY sort_order ASC, id ASC
            ''') as cursor:
                rows = await cursor.fetchall()

            for r in rows:
                category = {
                    "id": r['id'],
                    "name": r['name'],
                    "slug": r['slug'],
                    "keywords": []
                }

                # 获取关键词
                async with db.execute('''
                    SELECT keyword
                    FROM category_keywords
                    WHERE category_id = ?
                    ORDER BY weight DESC, id ASC
                ''', (r['id'],)) as keyword_cursor:
                    keyword_rows = await keyword_cursor.fetchall()
                    category["keywords"] = [kr['keyword'] for kr in keyword_rows]

                categories.append(category)

    except Exception as e:
        add_log('error', f'获取分类和关键词失败: {e}')

    return categories


async def create_category(data: Dict) -> int:
    """
    创建分类

    Args:
        data: 分类数据，包含 name, slug, description, icon, color, keywords, platforms

    Returns:
        新创建的分类ID
    """
    try:
        async with get_db() as db:
            # 插入分类
            await db.execute('''
                INSERT INTO categories (name, slug, description, icon, color, is_active, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('name'),
                data.get('slug'),
                data.get('description'),
                data.get('icon'),
                data.get('color'),
                data.get('is_active', True),
                data.get('sort_order', 0)
            ))

            # 获取新插入的ID
            async with db.execute("SELECT last_insert_rowid() as id") as cursor:
                row = await cursor.fetchone()
                category_id = row["id"]

            # 插入关键词
            if data.get('keywords'):
                for keyword in data['keywords']:
                    await db.execute('''
                        INSERT INTO category_keywords (category_id, keyword, weight)
                        VALUES (?, ?, ?)
                    ''', (category_id, keyword, 1))

            # 插入平台配置
            if data.get('platforms'):
                for platform in data['platforms']:
                    await db.execute('''
                        INSERT INTO category_platforms (category_id, platform, is_enabled)
                        VALUES (?, ?, ?)
                    ''', (category_id, platform, 1))

            await db.commit()
            add_log('success', f'创建分类成功: {data.get("name")}')
            return category_id

    except Exception as e:
        add_log('error', f'创建分类失败: {e}')
        raise


async def update_category(category_id: int, data: Dict) -> bool:
    """
    更新分类

    Args:
        category_id: 分类ID
        data: 要更新的数据

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            # 构建更新SQL
            update_fields = []
            update_values = []

            for field in ['name', 'slug', 'description', 'icon', 'color', 'is_active', 'sort_order']:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    update_values.append(data[field])

            if update_fields:
                update_values.append(category_id)
                await db.execute(f'''
                    UPDATE categories
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                ''', update_values)

            await db.commit()
            add_log('success', f'更新分类成功: {category_id}')
            return True

    except Exception as e:
        add_log('error', f'更新分类失败: {e}')
        return False


async def delete_category(category_id: int) -> bool:
    """
    删除分类

    Args:
        category_id: 分类ID

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            # 删除关键词（级联删除）
            await db.execute('DELETE FROM category_keywords WHERE category_id = ?', (category_id,))

            # 删除平台配置（级联删除）
            await db.execute('DELETE FROM category_platforms WHERE category_id = ?', (category_id,))

            # 删除分类
            await db.execute('DELETE FROM categories WHERE id = ?', (category_id,))

            await db.commit()
            add_log('success', f'删除分类成功: {category_id}')
            return True

    except Exception as e:
        add_log('error', f'删除分类失败: {e}')
        return False


async def update_category_keywords(category_id: int, keywords: List[str]) -> bool:
    """
    更新分类关键词

    Args:
        category_id: 分类ID
        keywords: 关键词列表

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            # 删除旧关键词
            await db.execute('DELETE FROM category_keywords WHERE category_id = ?', (category_id,))

            # 插入新关键词
            for keyword in keywords:
                await db.execute('''
                    INSERT INTO category_keywords (category_id, keyword, weight)
                    VALUES (?, ?, ?)
                ''', (category_id, keyword, 1))

            await db.commit()
            add_log('success', f'更新分类关键词成功: {category_id}')
            return True

    except Exception as e:
        add_log('error', f'更新分类关键词失败: {e}')
        return False


async def update_category_platforms(category_id: int, platforms: List[str]) -> bool:
    """
    更新分类平台配置

    Args:
        category_id: 分类ID
        platforms: 启用的平台列表

    Returns:
        是否成功
    """
    try:
        async with get_db() as db:
            # 删除旧配置
            await db.execute('DELETE FROM category_platforms WHERE category_id = ?', (category_id,))

            # 插入新配置
            for platform in platforms:
                await db.execute('''
                    INSERT INTO category_platforms (category_id, platform, is_enabled)
                    VALUES (?, ?, ?)
                ''', (category_id, platform, 1))

            await db.commit()
            return True

    except Exception as e:
        add_log('error', f'更新分类平台失败: {e}')
        return False


async def get_category_platforms(category_id: int) -> List[Dict]:
    """
    获取分类的平台配置

    Args:
        category_id: 分类ID

    Returns:
        平台列表
    """
    platforms = []
    try:
        async with get_db() as db:
            async with db.execute('''
                SELECT platform, is_enabled FROM category_platforms
                WHERE category_id = ?
            ''', (category_id,)) as cursor:
                rows = await cursor.fetchall()
                platforms = [dict(r) for r in rows]

    except Exception as e:
        add_log('error', f'获取分类平台失败: {e}')

    return platforms


async def init_default_categories() -> int:
    """
    初始化默认分类

    Returns:
        创建的分类数量
    """
    try:
        async with get_db() as db:
            created_count = 0
            default_platforms = ['weibo', 'zhihu', 'douyin', 'xiaohongshu', 'toutiao']

            for cat_data in DEFAULT_CATEGORIES:
                # 检查是否已存在
                async with db.execute(
                    "SELECT id FROM categories WHERE slug = ?",
                    (cat_data['slug'],)
                ) as cursor:
                    existing = await cursor.fetchone()

                if existing:
                    continue

                # 插入分类
                await db.execute('''
                    INSERT INTO categories (name, slug, description, icon, color, is_active, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cat_data['name'],
                    cat_data['slug'],
                    cat_data['description'],
                    cat_data['icon'],
                    cat_data['color'],
                    1,
                    created_count
                ))

                # 获取新插入的ID
                async with db.execute("SELECT last_insert_rowid() as id") as cursor:
                    row = await cursor.fetchone()
                    category_id = row["id"]

                # 插入关键词
                for keyword in cat_data['keywords']:
                    await db.execute('''
                        INSERT INTO category_keywords (category_id, keyword, weight)
                        VALUES (?, ?, ?)
                    ''', (category_id, keyword, 1))

                # 插入平台配置
                for platform in default_platforms:
                    await db.execute('''
                        INSERT INTO category_platforms (category_id, platform, is_enabled)
                        VALUES (?, ?, ?)
                    ''', (category_id, platform, 1))

                created_count += 1

            await db.commit()

            if created_count > 0:
                add_log('success', f'初始化默认分类完成，共创建 {created_count} 个分类')
            else:
                add_log('info', '默认分类已存在，无需初始化')

            return created_count

    except Exception as e:
        add_log('error', f'初始化默认分类失败: {e}')
        return 0
