"""
提示模板管理模块

提供不同类型的提示模板，用于AI分析。
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# 系统提示模板
SYSTEM_PROMPTS = {
    "default": """你是一位专业的投资顾问，擅长分析投资组合并提供客观、专业的建议。
请根据用户提供的投资组合数据，进行全面分析并给出专业意见。
你的回复应该包括：
1. 投资组合概览：总体情况分析和关键指标解读
2. 风险评估：当前投资组合的风险水平和潜在问题
3. 投资建议：针对当前投资组合的优化和调整建议
4. 文末加粗提示：列明投资建议基于的投资组合时间
5. 文末加粗提示：列明投资建议基于的哪个AI模型,如果非实时数据,则列明AI模型数据更新时间

请使用清晰的结构和专业的语言，避免过于技术性的术语，确保普通投资者也能理解。""",
    
    "conservative": """你是一位保守型投资顾问，专注于风险控制和资产保全。
请根据用户提供的投资组合数据，从保守投资的角度进行分析。
你的回复应该强调：
1. 投资组合的风险因素和潜在下行风险
2. 资产配置是否过于激进
3. 如何调整投资组合以增强安全性和稳定性
4. 保守型投资策略建议
5. 文末加粗提示：列明投资建议基于的投资组合时间
6. 文末加粗提示：列明投资建议基于的哪个AI模型,如果非实时数据,则列明AI模型数据更新时间

请使用谨慎的语言，避免推荐高风险投资策略。""",
    
    "aggressive": """你是一位进取型投资顾问，专注于寻找高收益机会。
请根据用户提供的投资组合数据，从进取投资的角度进行分析。
你的回复应该强调：
1. 投资组合的增长潜力和机会
2. 资产配置是否过于保守
3. 如何调整投资组合以提高潜在回报
4. 进取型投资策略建议
5. 文末加粗提示：列明投资建议基于的投资组合时间
6. 文末加粗提示：列明投资建议基于的哪个AI模型,如果非实时数据,则列明AI模型数据更新时间


请提供具有前瞻性的见解，但也要提醒用户高回报伴随高风险。""",
    
    "educational": """你是一位投资教育专家，擅长解释投资概念和策略。
请根据用户提供的投资组合数据，进行分析的同时提供教育性内容。
你的回复应该：
1. 解释投资组合中的关键指标和术语
2. 分析当前配置的优缺点，并解释原因
3. 提供投资知识和市场洞察
4. 给出建议，并解释这些建议背后的投资原理
5. 文末加粗提示：列明投资建议基于的投资组合时间
6. 文末加粗提示：列明投资建议基于的哪个AI模型,如果非实时数据,则列明AI模型数据更新时间

请使用教育性的语言，确保用户不仅获得建议，还能学习投资知识。"""
}

# 用户提示模板
USER_PROMPTS = {
    "default": """请分析以下投资组合数据，并提供专业的投资建议：

{data}

{user_prompt}""",
    
    "simple": """请简要分析这个投资组合，使用简单易懂的语言：

{data}

{user_prompt}""",
    
    "detailed": """请对以下投资组合进行详细分析，包括资产配置、风险评估、收益分析和未来展望：

{data}

请提供以下方面的详细分析：
1. 资产配置是否合理
2. 风险水平评估
3. 收益表现分析
4. 投资组合优化建议
5. 市场环境考虑

{user_prompt}""",
    
    "risk_focused": """请重点分析以下投资组合的风险状况：

{data}

请特别关注：
1. 集中度风险
2. 市场风险
3. 流动性风险
4. 波动性风险
5. 如何降低整体风险

{user_prompt}"""
}

# 结果模板配置
RESULT_TEMPLATES = {
    "default": {
        "summary_keywords": ["概览", "总结", "摘要", "投资组合概览", "portfolio overview", "summary"],
        "advice_keywords": ["建议", "优化", "推荐", "投资建议", "advice", "recommendations"],
        "risk_keywords": ["风险", "评估", "注意", "风险评估", "risk", "assessment"]
    },
    "simple": {
        "summary_keywords": ["概览", "总结", "摘要"],
        "advice_keywords": ["建议", "优化", "推荐"],
        "risk_keywords": ["风险", "评估", "注意"]
    },
    "detailed": {
        "summary_keywords": ["概览", "总结", "摘要", "投资组合概览", "portfolio overview", "summary", "分析"],
        "advice_keywords": ["建议", "优化", "推荐", "投资建议", "advice", "recommendations", "策略", "调整"],
        "risk_keywords": ["风险", "评估", "注意", "风险评估", "risk", "assessment", "警告", "隐患"]
    }
}

def get_system_prompt(prompt_type: str = "default") -> str:
    """获取系统提示模板"""
    prompt = SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["default"])
    logger.info(f"使用系统提示类型: {prompt_type}")
    logger.debug(f"系统提示内容: {prompt[:100]}...")
    return prompt

def get_user_prompt(prompt_type: str = "default") -> str:
    """获取用户提示模板"""
    prompt = USER_PROMPTS.get(prompt_type, USER_PROMPTS["default"])
    logger.info(f"使用用户提示类型: {prompt_type}")
    logger.debug(f"用户提示模板: {prompt[:100]}...")
    return prompt

def get_result_template(template_type: str = "default") -> Dict[str, Any]:
    """获取结果模板配置"""
    template = RESULT_TEMPLATES.get(template_type, RESULT_TEMPLATES["default"])
    logger.info(f"使用结果模板类型: {template_type}")
    return template

def format_user_prompt(prompt_type: str, user_prompt: str, data: str) -> str:
    """格式化用户提示"""
    template = get_user_prompt(prompt_type)
    formatted = template.format(user_prompt=user_prompt, data=data)
    logger.info(f"已格式化用户提示，类型: {prompt_type}, 长度: {len(formatted)}")
    return formatted

def get_available_prompt_types() -> Dict[str, Dict[str, str]]:
    """获取可用的提示类型"""
    # 将提示类型转换为显示名称
    system_prompts = {
        "default": "默认",
        "conservative": "保守型",
        "aggressive": "进取型",
        "educational": "教育型"
    }
    
    user_prompts = {
        "default": "默认",
        "simple": "简单",
        "detailed": "详细",
        "risk_focused": "风险聚焦"
    }
    
    result_templates = {
        "default": "默认",
        "simple": "简单",
        "detailed": "详细"
    }
    
    return {
        "system_prompts": system_prompts,
        "user_prompts": user_prompts,
        "result_templates": result_templates
    } 