"""
OPC Marketplace - 揭榜挂帅项目数据导入脚本
从江苏省属企业AI应用场景清单导入数据
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# 项目数据
GOVERNMENT_PROJECTS = [
    {
        "id": str(uuid4()),
        "title": "海上风电场智能运维系统",
        "project_code": "JSGX-AI-2024-001",
        "publisher_name": "江苏省国信集团有限公司",
        "publisher_type": "PROVINCIAL",
        "publisher_department": "能源部",
        "contact_person": "叶兴沛",
        "contact_phone": "18251862103",
        "industry": "新能源",
        "technology_field": ["人工智能", "物联网", "大数据"],
        "project_category": "TECH_RESEARCH",
        "budget_min": 2000000,
        "budget_max": 3000000,
        "currency": "CNY",
        "funding_source": "企业自筹",
        "description": """融合人工智能技术，在海上风电项目中搭建智能运维系统。主要功能包括：
1. 风机状态实时评估与监测
2. 远程运维控制
3. 无人巡检系统
4. 故障预测与预防性维护
5. 运维效率与安全性提升

项目目标：实现海上风电机组的无人巡检、故障预测维护，提升运维效率与安全性。""",
        "eligibility_requirements": """1. 具有独立法人资格
2. 在人工智能、物联网领域有相关技术积累
3. 有海上风电或类似工业场景的项目经验
4. 具备完善的售后服务体系""",
        "technical_requirements": """1. 支持多种传感器数据接入
2. 具备实时数据处理能力
3. 支持边缘计算和云端协同
4. 提供完整的API接口
5. 支持移动端和Web端访问""",
        "deliverables": """1. 智能运维系统软件平台
2. 硬件设备集成方案
3. 技术文档和用户手册
4. 培训和售后服务""",
        "evaluation_criteria": {
            "技术方案": 40,
            "项目经验": 25,
            "团队实力": 20,
            "报价合理性": 15
        },
        "project_duration": "12个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["海上风电", "智能运维", "无人巡检", "故障预测"],
        "is_featured": True,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "高速公路智慧化综合管理平台",
        "project_code": "JSGX-AI-2024-002",
        "publisher_name": "江苏交通控股有限公司",
        "publisher_type": "PROVINCIAL",
        "publisher_department": "科技信息部",
        "industry": "交通",
        "technology_field": ["人工智能", "物联网", "大数据", "5G"],
        "project_category": "INDUSTRIAL_UPGRADE",
        "budget_min": 5000000,
        "budget_max": 10000000,
        "currency": "CNY",
        "funding_source": "政府补贴+企业自筹",
        "description": """高速公路全路段智慧化改造项目，包括：
1. 智慧收费系统（ETC、无感支付）
2. 智慧监控系统（AI视频分析）
3. 智慧服务区（智能停车、智能餐饮）
4. 车路协同系统
5. 应急指挥调度系统

项目目标：打造全国领先的智慧高速公路示范路段。""",
        "eligibility_requirements": """1. 具有高速公路信息化项目经验
2. 具备系统集成资质
3. 有良好的财务状况和信誉
4. 具备本地化服务能力""",
        "project_duration": "18个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=45)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["智慧高速", "车路协同", "智能监控"],
        "is_featured": True,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "媒体产业全链路智能协同平台",
        "project_code": "JSGX-AI-2024-003",
        "publisher_name": "江苏省广播电视集团有限公司",
        "publisher_type": "PROVINCIAL",
        "publisher_department": "技术部",
        "industry": "文化传媒",
        "technology_field": ["人工智能", "自然语言处理", "知识图谱", "生成式AI"],
        "project_category": "PRODUCT_DEVELOPMENT",
        "budget_min": 1000000,
        "budget_max": 2000000,
        "currency": "CNY",
        "description": """媒体内容生产全流程智能化平台，包括：
1. 智能选题策划（热点分析、选题推荐）
2. 内容智能生成（新闻稿件、视频脚本）
3. 智能审核系统（内容合规、版权检测）
4. 智能分发系统（多平台一键发布）
5. 效果分析系统（传播效果追踪）

项目目标：提升媒体内容生产效率50%以上。""",
        "project_duration": "12个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["媒体智能化", "内容生产", "AIGC"],
        "is_featured": True,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "AI驱动的纺织设计系统",
        "project_code": "JSGX-AI-2024-004",
        "publisher_name": "江苏省苏豪控股集团有限公司",
        "publisher_type": "PROVINCIAL",
        "publisher_department": "设计中心",
        "industry": "纺织服装",
        "technology_field": ["人工智能", "生成式AI", "计算机视觉"],
        "project_category": "PRODUCT_DEVELOPMENT",
        "budget_min": 800000,
        "budget_max": 1500000,
        "currency": "CNY",
        "description": """利用AI技术辅助纺织品设计，包括：
1. 图案智能生成（基于风格迁移、GAN等技术）
2. 色彩搭配推荐
3. 款式设计辅助
4. 面料仿真预览
5. 设计方案评估

项目目标：缩短设计周期60%，提升设计创新性。""",
        "project_duration": "10个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["纺织设计", "AI生成", "创意设计"],
        "is_featured": False,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "智能验布与面料缺陷检测系统",
        "project_code": "JSGX-AI-2024-005",
        "publisher_name": "江苏省苏豪控股集团有限公司",
        "publisher_type": "PROVINCIAL",
        "industry": "纺织服装",
        "technology_field": ["人工智能", "计算机视觉", "深度学习"],
        "project_category": "PRODUCT_DEVELOPMENT",
        "budget_min": 500000,
        "budget_max": 1000000,
        "currency": "CNY",
        "description": """基于计算机视觉的智能验布系统：
1. 面料缺陷自动检测（断经、断纬、污渍等）
2. 缺陷分类和严重程度评估
3. 检测报告自动生成
4. 与生产系统对接

项目目标：实现99%以上的缺陷检出率，检测速度≥30米/分钟。""",
        "project_duration": "8个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["面料检测", "缺陷识别", "智能质检"],
        "is_featured": False,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "智慧农业无人机巡检平台",
        "project_code": "JSGX-AI-2024-006",
        "publisher_name": "江苏省农垦集团有限公司",
        "publisher_type": "PROVINCIAL",
        "publisher_department": "农业技术部",
        "industry": "农业",
        "technology_field": ["人工智能", "无人机", "遥感", "大数据"],
        "project_category": "INDUSTRIAL_UPGRADE",
        "budget_min": 1000000,
        "budget_max": 2000000,
        "currency": "CNY",
        "description": """农业无人机巡检及数据分析平台：
1. 无人机自动巡检航线规划
2. 作物生长状况监测
3. 病虫害智能识别
4. 产量预测模型
5. 农事决策建议

项目目标：实现10万亩农田的智能化管理。""",
        "project_duration": "12个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["智慧农业", "无人机", "精准农业"],
        "is_featured": True,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "煤矿智能洗选质量控制系统",
        "project_code": "JSGX-AI-2024-007",
        "publisher_name": "徐州矿务集团有限公司",
        "publisher_type": "PROVINCIAL",
        "publisher_department": "生产技术部",
        "industry": "煤炭",
        "technology_field": ["人工智能", "工业互联网", "大数据"],
        "project_category": "INDUSTRIAL_UPGRADE",
        "budget_min": 2000000,
        "budget_max": 4000000,
        "currency": "CNY",
        "description": """煤炭洗选工艺智能化控制系统：
1. 原煤质量在线检测
2. 洗选工艺参数智能优化
3. 产品质量实时监控
4. 能耗优化管理
5. 生产数据可视化

项目目标：提升精煤回收率3%，降低能耗10%。""",
        "project_duration": "12个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["煤炭洗选", "智能优化", "质量提升"],
        "is_featured": False,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "旧房改造AI协同设计平台",
        "project_code": "JSGX-AI-2024-008",
        "publisher_name": "中国江苏国际经济技术合作集团有限公司",
        "publisher_type": "PROVINCIAL",
        "publisher_department": "工程技术部",
        "industry": "建筑工程",
        "technology_field": ["人工智能", "BIM", "物联网"],
        "project_category": "INDUSTRIAL_UPGRADE",
        "budget_min": 1000000,
        "budget_max": 2000000,
        "currency": "CNY",
        "description": """旧房改造AI协同设计平台：
1. 房屋结构智能评估
2. 改造方案智能生成
3. BIM模型自动建模
4. 施工进度智能管理
5. 成本预算智能估算

项目目标：提升旧房改造设计效率40%，降低成本15%。""",
        "project_duration": "10个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["旧房改造", "智能建筑", "城市更新"],
        "is_featured": False,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "燃气轮机智能运维系统",
        "project_code": "JSGX-AI-2024-009",
        "publisher_name": "江苏省国信集团有限公司",
        "publisher_type": "PROVINCIAL",
        "industry": "能源",
        "technology_field": ["人工智能", "工业互联网", "大数据"],
        "project_category": "TECH_RESEARCH",
        "budget_min": 3000000,
        "budget_max": 5000000,
        "currency": "CNY",
        "description": """300MW级燃气轮机发电机组智能运维系统：
1. 设备状态实时监测
2. 故障预警与诊断
3. 预测性维护
4. 运维决策支持
5. 备件管理优化

项目目标：实现非计划停机时间减少50%。""",
        "project_duration": "15个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["燃气轮机", "智能运维", "故障预警"],
        "is_featured": False,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "智慧高速出行服务APP",
        "project_code": "JSGX-AI-2024-010",
        "publisher_name": "江苏交通控股有限公司",
        "publisher_type": "PROVINCIAL",
        "industry": "交通",
        "technology_field": ["人工智能", "大数据", "移动互联网"],
        "project_category": "PUBLIC_SERVICE",
        "budget_min": 2000000,
        "budget_max": 4000000,
        "currency": "CNY",
        "description": """基于AI的个性化出行服务系统：
1. 智能路线规划
2. 实时路况预测
3. 服务区推荐
4. ETC无感支付
5. 会员积分体系

项目目标：用户数达到500万，日活50万。""",
        "project_duration": "12个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["出行服务", "个性化推荐", "智慧高速"],
        "is_featured": False,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "安全生产智能管控平台",
        "project_code": "JSGX-AI-2024-011",
        "publisher_name": "江苏省苏豪控股集团有限公司",
        "publisher_type": "PROVINCIAL",
        "industry": "安全生产",
        "technology_field": ["人工智能", "物联网", "计算机视觉"],
        "project_category": "PUBLIC_SERVICE",
        "budget_min": 1500000,
        "budget_max": 2500000,
        "currency": "CNY",
        "description": """企业安全生产智能管控平台：
1. 视频AI安全监测
2. 隐患智能排查
3. 风险预警系统
4. 应急指挥调度
5. 安全培训管理

项目目标：实现安全事故率降低30%。""",
        "project_duration": "10个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["安全生产", "风险管控", "隐患排查"],
        "is_featured": False,
        "view_count": 0,
        "application_count": 0
    },
    {
        "id": str(uuid4()),
        "title": "煤矿大数据智能决策系统",
        "project_code": "JSGX-AI-2024-012",
        "publisher_name": "徐州矿务集团有限公司",
        "publisher_type": "PROVINCIAL",
        "industry": "煤炭",
        "technology_field": ["人工智能", "大数据", "知识图谱"],
        "project_category": "TECH_RESEARCH",
        "budget_min": 1500000,
        "budget_max": 3000000,
        "currency": "CNY",
        "description": """煤矿大数据智能决策支持系统：
1. 生产调度优化
2. 安全风险评估
3. 设备健康管理
4. 成本分析预测
5. 经营决策支持

项目目标：提升生产效率20%，降低运营成本10%。""",
        "project_duration": "12个月",
        "publish_date": datetime.now().isoformat(),
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "APPLICATION_OPEN",
        "region": "江苏省",
        "tags": ["煤矿大数据", "智能决策", "安全生产"],
        "is_featured": False,
        "view_count": 0,
        "application_count": 0
    }
]

def save_projects():
    """保存项目数据到JSON文件"""
    output_path = os.path.expanduser("~/Desktop/opc-marketplace/data/government_projects.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(GOVERNMENT_PROJECTS, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存 {len(GOVERNMENT_PROJECTS)} 个项目到: {output_path}")
    return output_path

def generate_sql_inserts():
    """生成SQL插入语句"""
    sql_statements = []
    
    for project in GOVERNMENT_PROJECTS:
        # 处理JSON字段
        technology_field = json.dumps(project.get('technology_field', []), ensure_ascii=False)
        evaluation_criteria = json.dumps(project.get('evaluation_criteria', {}), ensure_ascii=False)
        tags = json.dumps(project.get('tags', []), ensure_ascii=False)
        
        sql = f"""INSERT INTO government_projects (
    id, title, project_code, description, publisher_type, publisher_name,
    publisher_department, contact_person, contact_phone, industry,
    technology_field, project_category, budget_min, budget_max, currency,
    funding_source, publish_date, application_deadline, project_duration,
    eligibility_requirements, technical_requirements, deliverables,
    evaluation_criteria, status, region, tags, is_featured, view_count, application_count
) VALUES (
    '{project["id"]}',
    '{project["title"]}',
    '{project.get("project_code", "")}',
    '{project["description"].replace("'", "''")}',
    '{project["publisher_type"]}',
    '{project["publisher_name"]}',
    '{project.get("publisher_department", "")}',
    '{project.get("contact_person", "")}',
    '{project.get("contact_phone", "")}',
    '{project["industry"]}',
    '{technology_field}',
    '{project["project_category"]}',
    {project["budget_min"]},
    {project["budget_max"]},
    '{project["currency"]}',
    '{project.get("funding_source", "")}',
    '{project["publish_date"]}',
    '{project["application_deadline"]}',
    '{project.get("project_duration", "")}',
    '{project.get("eligibility_requirements", "").replace("'", "''")}',
    '{project.get("technical_requirements", "").replace("'", "''")}',
    '{project.get("deliverables", "").replace("'", "''")}',
    '{evaluation_criteria}',
    '{project["status"]}',
    '{project["region"]}',
    '{tags}',
    {project.get("is_featured", False)},
    {project.get("view_count", 0)},
    {project.get("application_count", 0)}
);"""
        sql_statements.append(sql)
    
    # 保存SQL文件
    sql_path = os.path.expanduser("~/Desktop/opc-marketplace/data/insert_projects.sql")
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(sql_statements))
    
    print(f"✅ 已生成SQL插入语句到: {sql_path}")
    return sql_path

if __name__ == "__main__":
    print("🚀 开始导入揭榜挂帅项目数据...")
    print("=" * 60)
    
    # 保存JSON数据
    json_path = save_projects()
    
    # 生成SQL语句
    sql_path = generate_sql_inserts()
    
    # 统计信息
    print("\n📊 数据统计:")
    print(f"- 总项目数: {len(GOVERNMENT_PROJECTS)}")
    
    # 按行业统计
    industries = {}
    for p in GOVERNMENT_PROJECTS:
        industry = p['industry']
        industries[industry] = industries.get(industry, 0) + 1
    
    print("\n按行业分布:")
    for industry, count in sorted(industries.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {industry}: {count}个项目")
    
    # 按预算统计
    total_budget = sum(p['budget_max'] for p in GOVERNMENT_PROJECTS)
    print(f"\n总预算金额: {total_budget/10000:.0f}万元")
    
    # 按发布方统计
    publishers = {}
    for p in GOVERNMENT_PROJECTS:
        publisher = p['publisher_name']
        publishers[publisher] = publishers.get(publisher, 0) + 1
    
    print("\n按发布方分布:")
    for publisher, count in sorted(publishers.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {publisher}: {count}个项目")
    
    print("\n" + "=" * 60)
    print("✅ 数据导入完成！")
    print(f"\n📁 数据文件:")
    print(f"  • JSON: {json_path}")
    print(f"  • SQL:  {sql_path}")