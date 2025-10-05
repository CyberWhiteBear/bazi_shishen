"""八字十神应用（Streamlit）

功能：
- 交互选择四柱（年/月/日/时）的天干与地支，依据日干计算对应的十神
- 同时输出直观的文字结果与结构化 JSON（支持性别与“时柱不详”的场景；地支十神按本气/中气/余气标注）
- 提供 JSON 下载，便于后续分析或系统集成

模块定位：
- 作为前端应用层，调用内部规则与映射，展示与导出结果
- 建议配合规则模块（如 bazi_shishen_rules.py）使用，便于复用与测试
"""

import streamlit as st
import json

def calculate_ten_gods(year_gan, year_zhi, month_gan, month_zhi, day_gan, day_zhi, hour_gan, hour_zhi):
    # 天干阴阳五行映射
    gan_info = {
        '甲': {'wuxing': '木', 'yinyang': '阳'},
        '乙': {'wuxing': '木', 'yinyang': '阴'},
        '丙': {'wuxing': '火', 'yinyang': '阳'},
        '丁': {'wuxing': '火', 'yinyang': '阴'},
        '戊': {'wuxing': '土', 'yinyang': '阳'},
        '己': {'wuxing': '土', 'yinyang': '阴'},
        '庚': {'wuxing': '金', 'yinyang': '阳'},
        '辛': {'wuxing': '金', 'yinyang': '阴'},
        '壬': {'wuxing': '水', 'yinyang': '阳'},
        '癸': {'wuxing': '水', 'yinyang': '阴'}
    }

    # 地支藏干表（本气、中气、余气）
    zhi_cang = {
        '子': [('癸', '本气')],
        '丑': [('己', '本气'), ('癸', '中气'), ('辛', '余气')],
        '寅': [('甲', '本气'), ('丙', '中气'), ('戊', '余气')],
        '卯': [('乙', '本气')],
        '辰': [('戊', '本气'), ('乙', '中气'), ('癸', '余气')],
        '巳': [('丙', '本气'), ('庚', '中气'), ('戊', '余气')],
        '午': [('丁', '本气'), ('己', '中气')],
        '未': [('己', '本气'), ('丁', '中气'), ('乙', '余气')],
        '申': [('庚', '本气'), ('壬', '中气'), ('戊', '余气')],
        '酉': [('辛', '本气')],
        '戌': [('戊', '本气'), ('辛', '中气'), ('丁', '余气')],
        '亥': [('壬', '本气'), ('甲', '中气')]
    }

    # 修正后的十神规则表
    ten_gods_rules = {
        'same': {  # 同我者
            'same': '比肩',   # 阴阳相同
            'diff': '劫财'    # 阴阳不同
        },
        'sheng_wo': {  # 生我者
            'same': '偏印',   # 阴阳相同
            'diff': '正印'    # 阴阳不同
        },
        'ke_wo': {  # 克我者
            'same': '七杀',   # 阴阳相同
            'diff': '正官'    # 阴阳不同
        },
        'wo_sheng': {  # 我生者
            'same': '食神',   # 阴阳相同
            'diff': '伤官'    # 阴阳不同
        },
        'wo_ke': {  # 我克者
            'same': '偏财',   # 阴阳相同
            'diff': '正财'    # 阴阳不同
        }
    }

    # 五行生克关系
    wuxing_relations = {
        '木': {
            'sheng_wo': '水',  # 生我者：水
            'wo_sheng': '火',  # 我生者：火
            'ke_wo': '金',     # 克我者：金
            'wo_ke': '土'      # 我克者：土
        },
        '火': {
            'sheng_wo': '木',  # 生我者：木
            'wo_sheng': '土',  # 我生者：土
            'ke_wo': '水',     # 克我者：水
            'wo_ke': '金'      # 我克者：金
        },
        '土': {
            'sheng_wo': '火',  # 生我者：火
            'wo_sheng': '金',  # 我生者：金
            'ke_wo': '木',     # 克我者：木
            'wo_ke': '水'      # 我克者：水
        },
        '金': {
            'sheng_wo': '土',  # 生我者：土
            'wo_sheng': '水',  # 我生者：水
            'ke_wo': '火',     # 克我者：火
            'wo_ke': '木'      # 我克者：木
        },
        '水': {
            'sheng_wo': '金',  # 生我者：金
            'wo_sheng': '木',  # 我生者：木
            'ke_wo': '土',     # 克我者：土
            'wo_ke': '火'      # 我克者：火
        }
    }

    def get_relation(day_wuxing, target_wuxing):
        """关系判断逻辑"""
        if day_wuxing == target_wuxing:
            return 'same'
        if wuxing_relations[day_wuxing]['sheng_wo'] == target_wuxing:
            return 'sheng_wo'
        if wuxing_relations[day_wuxing]['wo_sheng'] == target_wuxing:
            return 'wo_sheng'
        if wuxing_relations[day_wuxing]['ke_wo'] == target_wuxing:
            return 'ke_wo'
        if wuxing_relations[day_wuxing]['wo_ke'] == target_wuxing:
            return 'wo_ke'
        return None

    # 获取日干信息
    day_info = gan_info[day_gan]
    day_wuxing = day_info['wuxing']
    day_yinyang = day_info['yinyang']

    results = []

    # 处理四柱天干
    for gan, zhi, position in zip(
        [year_gan, month_gan, day_gan, hour_gan],
        [year_zhi, month_zhi, day_zhi, hour_zhi],
        ['年柱', '月柱', '日柱', '时柱']
    ):
        # 跳过不详的柱
        if gan not in gan_info or zhi not in zhi_cang:
            continue
        # 处理天干
        if position == '日柱' and gan == day_gan:
            results.append({
                "position": position,
                "type": "天干",
                "element": gan,
                "ten_god": "日主"
            })
        else:
            target_info = gan_info[gan]
            relation = get_relation(day_wuxing, target_info['wuxing'])
            if relation:
                # 使用目标天干与日干的阴阳关系
                yinyang_relation = 'same' if target_info['yinyang'] == day_yinyang else 'diff'
                god_type = ten_gods_rules[relation][yinyang_relation]
                results.append({
                    "position": position,
                    "type": "天干",
                    "element": gan,
                    "ten_god": god_type
                })
            else:
                results.append({
                    "position": position,
                    "type": "天干",
                    "element": gan,
                    "ten_god": "关系未定义"
                })

        # 处理地支藏干
        cang_gan_list = zhi_cang[zhi]
        for cang_gan, qi_type in cang_gan_list:
            target_info = gan_info[cang_gan]
            relation = get_relation(day_wuxing, target_info['wuxing'])
            if relation:
                # 使用目标天干与日干的阴阳关系
                yinyang_relation = 'same' if target_info['yinyang'] == day_yinyang else 'diff'
                god_type = ten_gods_rules[relation][yinyang_relation]
                results.append({
                    "position": position,
                    "type": "地支藏干",
                    "element": zhi,
                    "canggan": cang_gan,
                    "qi_type": qi_type,
                    "ten_god": god_type
                })
            else:
                results.append({
                    "position": position,
                    "type": "地支藏干",
                    "element": zhi,
                    "canggan": cang_gan,
                    "qi_type": qi_type,
                    "ten_god": "关系未定义"
                })

    return results


def build_structured_json(results):
    pillars = {}
    for r in results:
        pos = r['position']
        if pos not in pillars:
            pillars[pos] = {'天干': None, '地支': None, '藏干': {}}
        if r['type'] == '天干':
            pillars[pos]['天干'] = {'字': r['element'], '十神': r['ten_god']}
        else:
            pillars[pos]['地支'] = r['element']
            pillars[pos]['藏干'][r['qi_type']] = {'字': r['canggan'], '十神': r['ten_god']}
    # 保持柱顺序
    ordered_positions = ['年柱','月柱','日柱','时柱']
    ordered = {pos: pillars[pos] for pos in ordered_positions if pos in pillars}
    return ordered


def build_analysis_json(results, gender, hour_unknown):
    # 初始化结构（顶层包含性别；八字输入包含各柱）
    analysis = {
        "性别": gender,
        "八字输入": {
            "年柱": {"天干": "不详", "地支": "不详", "十神": {"天干十神": ["不详"], "地支十神": ["不详"]}},
            "月柱": {"天干": "不详", "地支": "不详", "十神": {"天干十神": ["不详"], "地支十神": ["不详"]}},
            "日柱": {"天干": "不详", "地支": "不详", "十神": {"天干十神": ["不详"], "地支十神": ["不详"]}},
            "时柱": {"天干": "不详", "地支": "不详", "十神": {"天干十神": ["不详"], "地支十神": ["不详"]}}
        }
    }
    # 若时柱不详，则移除"时柱"键
    if hour_unknown:
        analysis["八字输入"].pop("时柱", None)

    # 收集每柱的天干与地支十神
    # 先按柱聚合
    pillars = {}
    for r in results:
        pos = r['position']
        if pos not in pillars:
            pillars[pos] = {"天干": None, "地支": None, "天干十神": [], "地支十神_raw": {}}
        if r['type'] == '天干':
            pillars[pos]["天干"] = r["element"]
            # 日柱天干十神固定为"日元"
            tg = "日元" if pos == "日柱" else r["ten_god"]
            pillars[pos]["天干十神"] = [tg]
        else:
            pillars[pos]["地支"] = r["element"]
            # 按气序收集地支十神
            pillars[pos]["地支十神_raw"][r["qi_type"]] = r["ten_god"]
    # 写入到 analysis 结构，地支十神按 本气/中气/余气 顺序
    order_qi = ["本气", "中气", "余气"]
    positions = ["年柱","月柱","日柱"] if hour_unknown else ["年柱","月柱","日柱","时柱"]
    for pos in positions:
        col = analysis["八字输入"][pos]
        if pos in pillars:
            col["天干"] = pillars[pos]["天干"] if pillars[pos]["天干"] else "不详"
            col["地支"] = pillars[pos]["地支"] if pillars[pos]["地支"] else "不详"
            dz_map = {}
            for q in order_qi:
                if q in pillars[pos]["地支十神_raw"]:
                    dz_map[q] = pillars[pos]["地支十神_raw"][q]
            col["十神"]["天干十神"] = pillars[pos]["天干十神"] if pillars[pos]["天干十神"] else ["不详"]
            col["十神"]["地支十神"] = dz_map if dz_map else {"本气":"不详","中气":"不详","余气":"不详"}
    return analysis

def main():
    st.title("八字十神计算器")
    st.markdown("选择八字的天干地支，计算对应的十神关系")
    
    # 天干地支选项
    gan_options = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    zhi_options = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 创建下拉菜单
    col1, col2 = st.columns(2)
    with col1:
        year_gan = st.selectbox("年干", gan_options, index=0)
        month_gan = st.selectbox("月干", gan_options, index=0)
        day_gan = st.selectbox("日干", gan_options, index=0)
        hour_gan = st.selectbox("时干", gan_options, index=0)
    
    with col2:
        year_zhi = st.selectbox("年支", zhi_options, index=0)
        month_zhi = st.selectbox("月支", zhi_options, index=0)
        day_zhi = st.selectbox("日支", zhi_options, index=0)
        hour_zhi = st.selectbox("时支", zhi_options, index=0)
    
    # 性别与时柱不详
    gender = st.selectbox("性别", ["男","女"], index=0)
    hour_unknown = st.checkbox("时柱不详", value=False)
    include_advisor_prompt = st.checkbox("生成'四柱命理顾问提示词'JSON字段", value=False)
    include_yongshen_prompt = st.checkbox("生成'用神提示词'JSON字段", value=False)

    # 计算按钮
    if st.button("计算十神"):
        # 计算十神
        # 若时柱不详，标记为不详以便 JSON 输出，计算时跳过
        calc_hour_gan = hour_gan if not hour_unknown else "不详"
        calc_hour_zhi = hour_zhi if not hour_unknown else "不详"

        results = calculate_ten_gods(
            year_gan, year_zhi, 
            month_gan, month_zhi, 
            day_gan, day_zhi, 
            calc_hour_gan, calc_hour_zhi
        )
        
        # 显示原始结果
        st.subheader("十神计算结果")
        for result in results:
            if result["type"] == "天干":
                st.write(f"{result['position']}天干[{result['element']}]：{result['ten_god']}")
            else:
                st.write(f"{result['position']}地支[{result['element']}]的{result['qi_type']}[{result['canggan']}]：{result['ten_god']}")
        
        # 显示JSON格式结果（包含性别与八字输入）
        st.subheader("JSON格式结果")
        # 基础 JSON（不含提示词），先序列化供提示词嵌入使用
        analysis_json = build_analysis_json(results, gender, hour_unknown)
        base_compact_json = json.dumps(analysis_json, ensure_ascii=False, separators=(',', ':'))

        # 基础JSON（不含提示词）
        compact_json = json.dumps(analysis_json, ensure_ascii=False, separators=(',', ':'))
        st.code(compact_json, language='json')

        # 提供基础JSON下载链接
        st.download_button(
            label="下载基础JSON结果",
            data=compact_json,
            file_name='ten_gods_analysis.json',
            mime='application/json'
        )

        # 如果勾选了生成提示词复选框，生成独立的JSON文件
        if include_advisor_prompt:
            advisor_text = f"""我希望你扮演一位四柱（八字）命理顾问的角色。我将向你提供一个人的八字，你的任务是运用中国传统命理学来解读此人的八字命盘。你需要分析他们的天干地支，月令作用，是否有根气，五行流转，找出其用神与忌神，并提供关于其性格特质，潜在的人生命运走向的见解。你的解读应基于传统八字理论，并清楚地解释你的推理过程与分析依据。
此外，请根据其五行平衡情况，提供具体建议，帮助他们在事业方向，人际关系，健康状况或自我修养方面实现生活的和谐。如有必要，也可结合传统智慧给与文化或情感方面的指导。
我的第一个请求是：“我想为一个八字为{base_compact_json}的人进行八字命理分析”"""
            
            st.code(advisor_text, language='text')
            
            st.download_button(
                label="下载四柱命理顾问提示词",
                data=advisor_text,
                file_name='ten_gods_advisor_prompt.txt',
                mime='text/plain'
            )

        if include_yongshen_prompt:
            yongshen_text = f"""我希望你扮演一位四柱（八字）命理顾问的角色。我将向你提供一个人的八字，你的任务是运用中国传统命理学来解读此人的八字命盘。你需要分析他们的天干地支，月令作用，是否有根气，五行流转，找出其用神与忌神，用神取用方法为扶抑、病药、调候、专旺、通关五种，分别罗列。扶抑分为扶抑日元和月令两种情况，都需要考虑。并提供关于其性格特质，潜在的人生命运走向的见解。你的解读应基于传统八字理论，并清楚地解释你的推理过程与分析依据。
此外，请根据其五行平衡情况，提供具体建议，帮助他们在事业方向，人际关系，健康状况或自我修养方面实现生活的和谐。如有必要，也可结合传统智慧给与文化或情感方面的指导。
我的第一个请求是：“我想为一个八字为{base_compact_json}的人进行八字命理分析”"""
            
            st.code(yongshen_text, language='text')
            
            st.download_button(
                label="下载用神提示词",
                data=yongshen_text,
                file_name='ten_gods_yongshen_prompt.txt',
                mime='text/plain'
            )





if __name__ == "__main__":
    main()