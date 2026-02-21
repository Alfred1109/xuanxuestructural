"""
大模型助手模块 - AI增强分析
LLM Helper Module - AI-Enhanced Analysis
"""

import os
import json
from typing import Dict, Optional

# 尝试导入 OpenAI，如果没有安装则设为 None
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    print("提示：openai 包未安装，AI增强功能将不可用")


class LLMHelper:
    """大模型助手类"""
    
    def __init__(self):
        # 从环境变量获取API KEY
        self.api_key = os.getenv('ARK_API_KEY')
        
        if not OPENAI_AVAILABLE:
            print("警告：openai 包未安装，AI增强功能将不可用")
            self.client = None
        elif not self.api_key:
            print("警告：未设置 ARK_API_KEY 环境变量，AI增强功能将不可用")
            self.client = None
        else:
            self.client = OpenAI(
                base_url='https://ark.cn-beijing.volces.com/api/v3',
                api_key=self.api_key
            )
        
        self.model = "deepseek-v3-2-251201"
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        return self.client is not None
    
    def enhance_bazi_analysis(self, bazi_data: Dict) -> Optional[str]:
        """
        增强八字分析
        
        Args:
            bazi_data: 八字数据
        
        Returns:
            AI增强的分析文本
        """
        if not self.is_available():
            return None
        
        try:
            # 构建提示词
            prompt = f"""你是一位资深的命理学专家，请根据以下八字信息，提供专业、详细且易懂的命理分析。

八字信息：
- 年柱：{bazi_data['bazi']['year']}
- 月柱：{bazi_data['bazi']['month']}
- 日柱：{bazi_data['bazi']['day']}
- 时柱：{bazi_data['bazi']['hour']}

五行分布：
{json.dumps(bazi_data['wuxing_count'], ensure_ascii=False)}

格局信息：
- 格局类型：{bazi_data.get('advanced_analysis', {}).get('geju', {}).get('pattern_type', '未知')}
- 日主强弱：{bazi_data.get('advanced_analysis', {}).get('geju', {}).get('strength_level', '未知')}

请从以下几个方面进行分析：
1. 性格特点（基于五行和格局）
2. 事业发展方向
3. 财运分析
4. 感情婚姻
5. 健康注意事项
6. 人生建议

要求：
- 语言通俗易懂，避免过于专业的术语
- 分析要有逻辑性和连贯性
- 给出具体可行的建议
- 保持积极正面的态度
- 字数控制在500字左右
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM增强分析失败: {str(e)}")
            return None
    
    def enhance_liuyao_interpretation(self, liuyao_data: Dict) -> Optional[str]:
        """
        增强六爻解读
        
        Args:
            liuyao_data: 六爻数据
        
        Returns:
            AI增强的解读文本
        """
        if not self.is_available():
            return None
        
        try:
            gua_info = liuyao_data['gua_info']
            question = liuyao_data.get('question', '未指定问题')
            
            prompt = f"""你是一位精通周易六爻的占卜大师，请根据以下卦象信息，为问卜者提供详细的解读。

问卜问题：{question}

卦象信息：
- 本卦：{gua_info['bengua']['name']}
- 上卦：{gua_info['bengua']['shang_gua']['name']} ({gua_info['bengua']['shang_gua']['nature']})
- 下卦：{gua_info['bengua']['xia_gua']['name']} ({gua_info['bengua']['xia_gua']['nature']})
- 动爻：{', '.join([f"第{yao}爻" for yao in gua_info.get('dongyao', [])]) if gua_info.get('dongyao') else '无'}
- 变卦：{gua_info.get('biangua', {}).get('name', '无') if gua_info.get('dongyao') else '无'}

请从以下方面进行解读：
1. 卦象总体含义
2. 针对问题的具体分析
3. 当前形势判断
4. 发展趋势预测
5. 行动建议
6. 注意事项

要求：
- 结合问题给出针对性的解读
- 语言简洁明了，通俗易懂
- 既要客观分析，也要给出积极建议
- 字数控制在400字左右
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM增强解读失败: {str(e)}")
            return None
    
    def enhance_qimen_interpretation(self, qimen_data: Dict, matter_type: str = "通用") -> Optional[str]:
        """
        增强奇门遁甲解读
        
        Args:
            qimen_data: 奇门遁甲数据
            matter_type: 事项类型
        
        Returns:
            AI增强的解读文本
        """
        if not self.is_available():
            return None
        
        try:
            time_info = qimen_data['时间信息']
            dun_info = qimen_data['遁甲信息']
            best_dir = qimen_data['最佳方位']
            prediction = qimen_data['事项预测']
            
            prompt = f"""你是一位精通奇门遁甲的预测大师，请根据以下奇门遁甲盘信息，为问卜者提供详细的解读。

时间信息：
- 时间：{time_info['阳历']}
- 四柱：{time_info['年柱']} {time_info['月柱']} {time_info['日柱']} {time_info['时柱']}
- 遁甲：{dun_info['阴阳遁']} {dun_info['局数']}

事项类型：{matter_type}

最佳方位：{best_dir['最佳方位']} ({best_dir['吉凶']})
- 八门：{best_dir['详情']['八门']}
- 九星：{best_dir['详情']['九星']}

事项预测：
- 综合吉凶：{prediction['综合吉凶']}
- 最佳宫位：{prediction['最佳宫位']}
- 建议：{prediction['建议']}

请从以下方面进行解读：
1. 当前时局的整体分析
2. 针对"{matter_type}"事项的具体预测
3. 最佳行动方位和时机
4. 需要注意的不利因素
5. 具体的行动建议
6. 成功概率和关键要点

要求：
- 结合奇门遁甲理论进行专业分析
- 语言通俗易懂，避免过于晦涩
- 给出实用可行的建议
- 保持客观理性的态度
- 字数控制在500字左右
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM增强解读失败: {str(e)}")
            return None
    
    def enhance_zeri_advice(self, zeri_data: Dict, purpose: str = "通用") -> Optional[str]:
        """
        增强择日建议
        
        Args:
            zeri_data: 择日数据
            purpose: 用途
        
        Returns:
            AI增强的建议文本
        """
        if not self.is_available():
            return None
        
        try:
            prompt = f"""你是一位精通择日学的专家，请根据以下日期信息，为用户提供详细的择日建议。

日期信息：
- 日期：{zeri_data['date']} {zeri_data.get('weekday', '')}
- 干支：{zeri_data['ganzhi']}
- 建星：{zeri_data['jianxing']}
- 十二神：{zeri_data['shier_shen']} ({zeri_data['huangdao_type']})
- 星宿：{zeri_data['xingxiu']}
- 吉凶等级：{zeri_data['level']} (评分：{zeri_data['score']})
- 宜：{', '.join(zeri_data['suitable'])}
- 忌：{', '.join(zeri_data['avoid'])}

用途：{purpose}

请提供：
1. 这一天的整体运势分析
2. 是否适合进行"{purpose}"相关的事务
3. 具体的时辰建议（如果适合的话）
4. 需要注意的事项
5. 其他建议

要求：
- 语言通俗易懂
- 给出实用的建议
- 保持客观理性
- 字数控制在300字左右
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM增强建议失败: {str(e)}")
            return None
    
    def chat(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """
        通用对话功能
        
        Args:
            question: 用户问题
            context: 上下文信息
        
        Returns:
            AI回复
        """
        if not self.is_available():
            return None
        
        try:
            system_prompt = """你是一位精通中国传统玄学的专家，包括八字命理、六爻占卜、择日学、风水学等。
你的回答应该：
1. 专业准确，基于传统理论
2. 通俗易懂，避免过于晦涩
3. 客观理性，不夸大其词
4. 积极正面，给人希望和方向
5. 实用可行，提供具体建议

请用简洁明了的语言回答用户的问题。"""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                messages.append({"role": "assistant", "content": f"相关信息：{context}"})
            
            messages.append({"role": "user", "content": question})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM对话失败: {str(e)}")
            return None


# 全局实例
llm_helper = LLMHelper()


if __name__ == "__main__":
    # 测试
    print("=== LLM助手测试 ===\n")
    
    if llm_helper.is_available():
        print("✓ LLM服务可用")
        
        # 测试对话
        response = llm_helper.chat("什么是八字命理？")
        if response:
            print(f"\n问题：什么是八字命理？")
            print(f"回答：{response}")
    else:
        print("✗ LLM服务不可用")
        print("请设置环境变量 ARK_API_KEY")
        print("Windows: set ARK_API_KEY=your_api_key")
        print("Linux/Mac: export ARK_API_KEY=your_api_key")
