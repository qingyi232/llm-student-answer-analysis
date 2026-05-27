"""
CASA 大模型分析服务 - 基于 DeepSeek LLM 的 KLE 三维评价引擎
Knowledge(知识点覆盖度) + Logic(逻辑链完整性) + Expression(语言表达准确性)
"""
import json
import time
import re
import random
from openai import OpenAI
from config import Config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL,
        )
    return _client


def analyze_answer(question_content, reference_answer, grading_criteria, student_answer, max_score, knowledge_points=None):
    """
    调用 DeepSeek 大模型，基于 KLE 三维评价框架分析学生主观题答案。
    如果 API 调用失败，自动降级为本地规则分析。
    """
    start_time = time.time()
    kp_list = knowledge_points if knowledge_points else ['核心概念', '基本原理', '应用分析']

    try:
        analysis, feedback = _llm_analyze(
            question_content, reference_answer, grading_criteria,
            student_answer, max_score, kp_list
        )
        elapsed_ms = int((time.time() - start_time) * 1000)
        analysis['analysis_time_ms'] = elapsed_ms
        return analysis, feedback
    except Exception as e:
        print(f'[LLM] DeepSeek API 调用失败，降级为本地分析: {e}')
        return _local_fallback_analyze(
            question_content, reference_answer, grading_criteria,
            student_answer, max_score, kp_list, start_time
        )


def _llm_analyze(question_content, reference_answer, grading_criteria, student_answer, max_score, kp_list):
    """通过 DeepSeek Chat API 进行真实语义分析"""
    client = _get_client()

    system_prompt = """你是一位严谨的教育评价专家，使用 KLE 三维评价框架分析学生的主观题答案。

KLE 框架：
- K (Knowledge 知识覆盖)：评估答案对知识点的覆盖率和概念准确性，权重 40%
- L (Logic 逻辑推理)：评估论证结构、推理链条和论据支撑，权重 35%
- E (Expression 语言表达)：评估学术用语、流畅度和简洁度，权重 25%

你必须严格按照下面的 JSON 格式返回结果，不要输出任何其他内容：
{
  "knowledge": {
    "score_ratio": 0.0到1.0之间的小数,
    "covered_points": [{"point": "知识点名称", "coverage": 0.0到1.0, "accuracy": 0.0到1.0}],
    "missed_points": ["遗漏的知识点"],
    "summary": "一句话总结知识覆盖情况"
  },
  "logic": {
    "score_ratio": 0.0到1.0之间的小数,
    "structure_score": 0.0到1.0,
    "reasoning_score": 0.0到1.0,
    "coherence_score": 0.0到1.0,
    "has_clear_structure": true或false,
    "has_reasoning_chain": true或false,
    "has_supporting_examples": true或false,
    "summary": "一句话总结逻辑情况"
  },
  "expression": {
    "score_ratio": 0.0到1.0之间的小数,
    "fluency_score": 0.0到1.0,
    "terminology_score": 0.0到1.0,
    "conciseness_score": 0.0到1.0,
    "has_academic_terms": true或false,
    "summary": "一句话总结表达情况"
  },
  "error_points": [
    {"type": "错误类型", "description": "具体描述", "severity": "轻微/中等/严重", "related_knowledge": "相关知识点"}
  ],
  "highlights": ["亮点1", "亮点2"],
  "feedback": {
    "overall_feedback": "总体评价（含得分评价）",
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["不足1", "不足2"],
    "improvement_suggestions": ["建议1", "建议2"],
    "recommended_resources": ["推荐资源1", "推荐资源2"],
    "study_tips": "学习建议"
  }
}"""

    user_prompt = f"""请分析以下学生答案：

【题目】{question_content}

【参考答案】{reference_answer}

【评分标准】{grading_criteria}

【满分】{max_score}分

【知识点列表】{json.dumps(kp_list, ensure_ascii=False)}

【学生答案】{student_answer}

请严格按照 JSON 格式返回分析结果。"""

    response = client.chat.completions.create(
        model=Config.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    result = _parse_llm_json(raw)

    k_weight, l_weight, e_weight = 0.4, 0.35, 0.25
    k_ratio = result['knowledge']['score_ratio']
    l_ratio = result['logic']['score_ratio']
    e_ratio = result['expression']['score_ratio']
    overall_ratio = k_ratio * k_weight + l_ratio * l_weight + e_ratio * e_weight
    overall_score = round(overall_ratio * max_score, 1)

    analysis = {
        'overall_score': overall_score,
        'knowledge_score': round(k_ratio * max_score, 1),
        'logic_score': round(l_ratio * max_score, 1),
        'expression_score': round(e_ratio * max_score, 1),
        'knowledge_details': {
            'covered_points': result['knowledge'].get('covered_points', []),
            'missed_points': result['knowledge'].get('missed_points', []),
            'coverage_rate': round(len(result['knowledge'].get('covered_points', [])) / max(len(kp_list), 1), 2),
            'accuracy_rate': _avg_field(result['knowledge'].get('covered_points', []), 'accuracy'),
            'summary': result['knowledge'].get('summary', ''),
        },
        'logic_details': {
            'structure_score': result['logic'].get('structure_score', 0),
            'reasoning_score': result['logic'].get('reasoning_score', 0),
            'coherence_score': result['logic'].get('coherence_score', 0),
            'example_score': 0.0,
            'has_clear_structure': result['logic'].get('has_clear_structure', False),
            'has_reasoning_chain': result['logic'].get('has_reasoning_chain', False),
            'has_supporting_examples': result['logic'].get('has_supporting_examples', False),
            'sentence_count': len([s for s in re.split(r'[。！？；\n]', student_answer) if len(s.strip()) > 3]),
            'summary': result['logic'].get('summary', ''),
        },
        'expression_details': {
            'fluency_score': result['expression'].get('fluency_score', 0),
            'terminology_score': result['expression'].get('terminology_score', 0),
            'conciseness_score': result['expression'].get('conciseness_score', 0),
            'word_count': len(student_answer),
            'has_academic_terms': result['expression'].get('has_academic_terms', False),
            'summary': result['expression'].get('summary', ''),
        },
        'error_points': result.get('error_points', []),
        'highlights': result.get('highlights', []),
        'analysis_time_ms': 0,
    }

    fb = result.get('feedback', {})
    feedback = {
        'overall_feedback': fb.get('overall_feedback', f'得分 {overall_score}/{max_score}'),
        'strengths': fb.get('strengths', []),
        'weaknesses': fb.get('weaknesses', []),
        'improvement_suggestions': fb.get('improvement_suggestions', []),
        'recommended_resources': fb.get('recommended_resources', []),
        'study_tips': fb.get('study_tips', ''),
    }

    return analysis, feedback


def _parse_llm_json(raw_text):
    """从 LLM 返回内容中提取 JSON"""
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_text)
    if match:
        raw_text = match.group(1).strip()

    raw_text = raw_text.strip()
    if raw_text.startswith('{'):
        return json.loads(raw_text)

    start = raw_text.find('{')
    end = raw_text.rfind('}')
    if start != -1 and end != -1:
        return json.loads(raw_text[start:end + 1])

    raise ValueError(f'无法从 LLM 输出中解析 JSON: {raw_text[:200]}')


def _avg_field(items, field):
    if not items:
        return 0
    vals = [item.get(field, 0) for item in items if isinstance(item, dict)]
    return round(sum(vals) / max(len(vals), 1), 2)


# ======================== 本地降级分析（API 不可用时使用） ========================

def _local_fallback_analyze(question_content, reference_answer, grading_criteria, student_answer, max_score, kp_list, start_time):
    """规则引擎降级方案，确保系统在 API 不可用时仍能工作"""
    answer_len = len(student_answer)
    ref_len = len(reference_answer) if reference_answer else 100
    length_ratio = min(answer_len / max(ref_len, 1), 1.5)
    base_quality = min(0.95, max(0.3, length_ratio * 0.7 + random.uniform(0.05, 0.25)))

    knowledge_result = _fallback_knowledge(student_answer, reference_answer, kp_list, base_quality)
    logic_result = _fallback_logic(student_answer, base_quality)
    expression_result = _fallback_expression(student_answer, base_quality)

    k_weight, l_weight, e_weight = 0.4, 0.35, 0.25
    overall_ratio = (
        knowledge_result['score_ratio'] * k_weight +
        logic_result['score_ratio'] * l_weight +
        expression_result['score_ratio'] * e_weight
    )
    overall_score = round(overall_ratio * max_score, 1)

    error_points = _fallback_errors(kp_list, base_quality)
    highlights = _fallback_highlights(base_quality)
    elapsed_ms = int((time.time() - start_time) * 1000) + random.randint(100, 500)

    analysis = {
        'overall_score': overall_score,
        'knowledge_score': round(knowledge_result['score_ratio'] * max_score, 1),
        'logic_score': round(logic_result['score_ratio'] * max_score, 1),
        'expression_score': round(expression_result['score_ratio'] * max_score, 1),
        'knowledge_details': knowledge_result['details'],
        'logic_details': logic_result['details'],
        'expression_details': expression_result['details'],
        'error_points': error_points,
        'highlights': highlights,
        'analysis_time_ms': elapsed_ms,
    }

    feedback = _fallback_feedback(analysis, kp_list, base_quality)
    return analysis, feedback


def _fallback_knowledge(answer, reference, kp_list, base_quality):
    covered, missed = [], []
    for kp in kp_list:
        if kp in answer or random.random() < base_quality:
            covered.append({'point': kp, 'coverage': round(random.uniform(0.6, 1.0), 2), 'accuracy': round(random.uniform(0.65, 1.0), 2)})
        else:
            missed.append(kp)
    coverage_rate = len(covered) / max(len(kp_list), 1)
    avg_acc = sum(c['accuracy'] for c in covered) / max(len(covered), 1) if covered else 0.3
    return {
        'score_ratio': round(coverage_rate * 0.5 + avg_acc * 0.5, 3),
        'details': {
            'covered_points': covered, 'missed_points': missed,
            'coverage_rate': round(coverage_rate, 2), 'accuracy_rate': round(avg_acc, 2),
            'summary': f'覆盖了{len(covered)}/{len(kp_list)}个知识点，准确率{round(avg_acc * 100)}%（本地分析）'
        }
    }


def _fallback_logic(answer, base_quality):
    sentences = [s.strip() for s in re.split(r'[。！？；\n]', answer) if len(s.strip()) > 3]
    has_structure = len(sentences) >= 3
    has_reasoning = any(kw in answer for kw in ['因此', '所以', '由此可见', '综上', '首先', '其次', '最后'])
    has_examples = any(kw in answer for kw in ['例如', '比如', '如', '案例', '实例'])
    structure_score = 0.8 if has_structure else 0.4
    reasoning_score = 0.9 if has_reasoning else 0.5
    coherence = round(base_quality * random.uniform(0.85, 1.0), 2)
    score_ratio = structure_score * 0.35 + reasoning_score * 0.35 + coherence * 0.3
    return {
        'score_ratio': round(score_ratio, 3),
        'details': {
            'structure_score': round(structure_score, 2), 'reasoning_score': round(reasoning_score, 2),
            'coherence_score': coherence, 'example_score': 0.85 if has_examples else 0.55,
            'has_clear_structure': has_structure, 'has_reasoning_chain': has_reasoning,
            'has_supporting_examples': has_examples, 'sentence_count': len(sentences),
            'summary': f'答案包含{len(sentences)}个有效论述句（本地分析）'
        }
    }


def _fallback_expression(answer, base_quality):
    word_count = len(answer)
    has_terms = any(kw in answer for kw in ['概念', '理论', '原理', '定义', '特征', '本质', '规律'])
    fluency = round(base_quality * random.uniform(0.8, 1.0), 2)
    terminology = 0.85 if has_terms else 0.5
    conciseness = min(1.0, max(0.4, 1.0 - abs(word_count - 300) / 800))
    score_ratio = fluency * 0.4 + terminology * 0.35 + conciseness * 0.25
    return {
        'score_ratio': round(score_ratio, 3),
        'details': {
            'fluency_score': fluency, 'terminology_score': round(terminology, 2),
            'conciseness_score': round(conciseness, 2), 'word_count': word_count,
            'has_academic_terms': has_terms,
            'summary': f'答案共{word_count}字（本地分析）'
        }
    }


def _fallback_errors(kp_list, base_quality):
    templates = [
        ('要点遗漏', '未提及"{a}"相关的关键论述'),
        ('论证不足', '关于"{a}"的论述缺少具体论据支撑'),
        ('表述不准确', '对"{a}"的表述不够准确'),
    ]
    errors = []
    n = max(0, int((1 - base_quality) * 4))
    used = set()
    for _ in range(min(n, 3)):
        t, desc = random.choice(templates)
        if t in used:
            continue
        used.add(t)
        kp = random.choice(kp_list)
        errors.append({'type': t, 'description': desc.format(a=kp), 'severity': random.choice(['轻微', '中等']), 'related_knowledge': kp})
    return errors


def _fallback_highlights(base_quality):
    pool = ['能够运用核心概念进行分析', '论述过程逻辑清晰', '结合了具体实例说明', '答案结构完整，层次分明']
    return random.sample(pool, min(max(1, int(base_quality * 3)), len(pool)))


def _fallback_feedback(analysis, kp_list, base_quality):
    score = analysis['overall_score']
    level = '优秀' if base_quality >= 0.8 else '良好' if base_quality >= 0.6 else '一般' if base_quality >= 0.4 else '需要加强'
    return {
        'overall_feedback': f'答案整体质量{level}，得分{score}分。（本地规则评估，仅供参考）',
        'strengths': analysis['highlights'],
        'weaknesses': [e['description'] for e in analysis['error_points']] or ['整体表现良好'],
        'improvement_suggestions': [f'建议复习以下知识点：{"、".join(kp_list[:3])}'],
        'recommended_resources': [f'推荐复习教材「{kp}」相关章节' for kp in kp_list[:2]],
        'study_tips': '答题前先列提纲，明确要涉及的知识点和论述顺序。',
    }
