from flask import Flask, request, jsonify, send_file
from keyword_manager import KeywordManager
import random
import os

app = Flask(__name__, static_folder="static", static_url_path="")

# 初始化关键词管理器（使用TXT文件存储）
SHARED_FILE = "灵感词库.txt"       # 共享词库（会被修改）
DEFAULT_FILE = "灵感词库_默认.txt"  # 默认词库（永不改变，只读）
keyword_mgr = KeywordManager(SHARED_FILE)
shared_mgr = KeywordManager(SHARED_FILE)  # 增删操作始终走共享文件
current_source = "shared"  # "shared" 或 "default"

# 管理密码：删除词汇时需要，添加词汇无需密码
MANAGE_PASSWORD = "admin888"

# 分类映射
CATEGORY_NAMES = {
    "ancient_materials": "古代素材",
    "republican_materials": "民国素材",
    "modern_materials": "现代素材",
    "colors": "主色调",
    "male_celebrities": "男明星",
    "female_celebrities": "女明星",
    "styles": "人物主题",
    "poems": "古诗歌词"
}

ERA_KEYS = {
    "ancient": "ancient_materials",
    "republican": "republican_materials",
    "modern": "modern_materials"
}


@app.route("/")
def index():
    """主页面 - 返回 Vue SPA"""
    return send_file("static/index.html")


@app.route("/api/categories")
def get_categories():
    """获取所有分类及其关键词数量"""
    categories = {}
    for key, name in CATEGORY_NAMES.items():
        keywords = keyword_mgr.get_category_keywords(key)
        categories[key] = {
            "name": name,
            "count": len(keywords),
            "keywords": keywords
        }
    return jsonify(categories)


@app.route("/api/generate", methods=["POST"])
def generate():
    """生成灵感组合"""
    data = request.get_json()
    mode = data.get("mode", "no_people")  # "people" 或 "no_people"

    if mode == "people":
        return generate_people(data)
    else:
        return generate_no_people(data)


def generate_people(data):
    """生成人物图灵感"""
    male_count = int(data.get("male_count", 1))
    female_count = int(data.get("female_count", 1))
    style_count = int(data.get("style_count", 1))

    male = keyword_mgr.get_random_keywords("male_celebrities", male_count)
    female = keyword_mgr.get_random_keywords("female_celebrities", female_count)
    styles = keyword_mgr.get_random_keywords("styles", style_count)

    result = {"title": "人物灵感组合", "items": []}

    if male:
        result["items"].append({"label": "男明星", "category": "male_celebrities", "values": male})
    if female:
        result["items"].append({"label": "女明星", "category": "female_celebrities", "values": female})
    if styles:
        result["items"].append({"label": "人物主题", "category": "styles", "values": styles})

    return jsonify(result)


def generate_no_people(data):
    """生成无人物图灵感"""
    era = data.get("era", "ancient")
    material_count = int(data.get("material_count", 2))
    color_count = int(data.get("color_count", 1))
    poem_count = int(data.get("poem_count", 0))

    colors = keyword_mgr.get_random_keywords("colors", color_count)

    era_name_map = {
        "ancient": "古代",
        "republican": "民国",
        "modern": "现代",
        "mixed": "混池"
    }
    era_name = era_name_map.get(era, "未知")

    if era == "mixed":
        # 混池：随机从三个时代抽取
        era_keys = list(ERA_KEYS.values())
        materials = []
        era_labels = []
        for _ in range(material_count):
            chosen = random.choice(era_keys)
            mat = keyword_mgr.get_random_keywords(chosen, 1)
            if mat:
                materials.append(mat[0])
                name_map = {
                    "ancient_materials": "(古代)",
                    "republican_materials": "(民国)",
                    "modern_materials": "(现代)"
                }
                era_labels.append(name_map.get(chosen, ""))
    else:
        era_key = ERA_KEYS.get(era, "ancient_materials")
        materials = keyword_mgr.get_random_keywords(era_key, material_count)
        era_labels = []

    result = {"title": f"无人物灵感组合 - {era_name}", "items": []}

    if materials:
        if era_labels:
            # 混池：每个material来自不同era，存储各自的category
            result["items"].append({
                "label": "素材",
                "category": "mixed",
                "values": [f"{m}{l}" for m, l in zip(materials, era_labels)]
            })
        else:
            result["items"].append({"label": "素材", "category": era_key, "values": materials})

    if color_count > 0 and colors:
        result["items"].append({"label": "主色调", "category": "colors", "values": colors})

    # 古代模式可选诗句
    if era == "ancient" and poem_count > 0:
        poems = keyword_mgr.get_random_keywords("poems", poem_count)
        if poems:
            result["items"].append({"label": "古诗歌词", "category": "poems", "values": poems})

    return jsonify(result)


@app.route("/api/keywords/random", methods=["POST"])
def random_keyword():
    """获取指定分类的随机关键词"""
    data = request.get_json()
    category = data.get("category", "")
    count = int(data.get("count", 1))
    count = max(1, min(count, 10))

    if category == "mixed":
        # 混池：从三个时代随机抽取
        era_keys = list(ERA_KEYS.values())
        results = []
        for _ in range(count):
            chosen = random.choice(era_keys)
            kw = keyword_mgr.get_random_keywords(chosen, 1)
            if kw:
                name_map = {
                    "ancient_materials": "(古代)",
                    "republican_materials": "(民国)",
                    "modern_materials": "(现代)"
                }
                results.append(kw[0] + name_map.get(chosen, ""))
        return jsonify({"keywords": results})
    else:
        keywords = keyword_mgr.get_random_keywords(category, count)
        return jsonify({"keywords": keywords})


@app.route("/api/keywords/add", methods=["POST"])
def add_keyword():
    """添加关键词"""
    data = request.get_json()
    category = data.get("category", "")
    keyword = data.get("keyword", "").strip()

    if not category or not keyword:
        return jsonify({"success": False, "message": "分类和关键词不能为空"}), 400

    success = shared_mgr.add_keyword(category, keyword)
    if success:
        # 如果当前正在查看共享词库，同步刷新
        if current_source == "shared":
            keyword_mgr.switch_file(SHARED_FILE)
        return jsonify({"success": True, "message": f"已添加: {keyword}"})
    else:
        return jsonify({"success": False, "message": "词汇已存在或无效"}), 400


@app.route("/api/keywords/delete", methods=["POST"])
def delete_keyword():
    """删除关键词（需要密码）"""
    data = request.get_json()
    category = data.get("category", "")
    keyword = data.get("keyword", "").strip()
    password = data.get("password", "")

    if not category or not keyword:
        return jsonify({"success": False, "message": "分类和关键词不能为空"}), 400

    if password != MANAGE_PASSWORD:
        return jsonify({"success": False, "message": "管理密码错误，无删除权限"}), 403

    success = shared_mgr.remove_keyword(category, keyword)
    if success:
        if current_source == "shared":
            keyword_mgr.switch_file(SHARED_FILE)
        return jsonify({"success": True, "message": f"已删除: {keyword}"})
    else:
        return jsonify({"success": False, "message": "删除失败，词汇不存在"}), 400


@app.route("/api/keywords/source")
def get_keywords_source():
    """获取当前词库来源"""
    return jsonify({"source": current_source})


@app.route("/api/keywords/switch_source", methods=["POST"])
def switch_keywords_source():
    """切换词库来源：shared <-> default"""
    global current_source
    target = request.get_json().get("source", "")
    if target == "shared":
        keyword_mgr.switch_file(SHARED_FILE)
        current_source = "shared"
    elif target == "default":
        keyword_mgr.switch_file(DEFAULT_FILE)
        current_source = "default"
    else:
        return jsonify({"success": False, "message": "无效的词库来源"}), 400
    return jsonify({"success": True, "source": current_source})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
