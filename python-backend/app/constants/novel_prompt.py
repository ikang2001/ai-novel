"""小说相关 Prompt 模板"""


class NovelPromptConstant:
    """小说生成 Prompt 常量"""

    # ========== Agent 1：设定助手 ==========

    AGENT1_SETTING_PROMPT = """
你是一位资深的小说策划师，擅长构建小说世界观和角色体系。

请根据以下信息，为用户创建小说的初始设定：

【基本信息】
书名：{title}
题材：{genre}
目标读者：{target_readers}
核心创意：{core_idea}
{initial_characters_section}

请以 JSON 格式输出，包含以下内容：

1. world_setting（世界观设定）：
   - era：时代背景
   - rules：核心规则/体系
   - factions：主要势力/阵营
   - locations：重要地点列表

2. characters（初始角色列表，至少包含主角）：
   - name：角色名
   - role_type：protagonist/supporting/antagonist/minor
   - age：年龄
   - personality：性格
   - appearance：外貌
   - skills：技能列表
   - background：背景故事
   - motivation：核心动机

3. volume_outline（卷级大纲，2-4卷）：
   - volume：卷号
   - title：卷标题
   - summary：本卷概要

注意：
- 角色设定要有层次感，主角需要有明确的成长弧光
- 世界观规则要自洽，不能有逻辑矛盾
- 卷级大纲要有递进关系，每卷有独立冲突
"""

    # ========== Agent 2：风格分析 ==========

    AGENT2_STYLE_ANALYZE_PROMPT = """
你是一位文学评论家和写作教练。请分析以下小说样本的写作风格，提取关键特征。

【样本内容】
{samples}

请以 JSON 格式输出风格分析，包含以下维度：

1. narrative_perspective：叙述视角（第一/第三人称，全知/限知）
2. language_style：语言风格（简洁/华丽/口语化等）
3. dialogue_style：对话风格（占比、特点、角色区分度）
4. description_preference：描写偏好（动作/心理/环境的比例）
5. rhythm：节奏特点（快慢交替、章末处理）
6. techniques：常用修辞手法列表
7. forbidden_words：作者明显避免使用的词列表
8. forbidden_patterns：作者明显避免的句式列表
9. sample_sentences：3-5个最能代表作者风格的句子
10. chapter_opening_style：章节开头习惯
11. chapter_ending_style：章节结尾习惯
12. emotional_tone：整体情感基调

注意：要提取的是作者的"写作指纹"，不是内容特征。
"""

    # ========== Agent 3：大纲助手 ==========

    AGENT3_OUTLINE_PROMPT = """
你是一位小说大纲规划师。请根据以下信息，为下一章生成详细大纲。

【小说信息】
书名：{title}
题材：{genre}
当前进度：第{chapter_number}章，第{volume_number}卷

【当前角色状态】
{character_states}

【最近章节摘要】
{recent_summaries}

【活跃伏笔】
{active_foreshadowing}

{author_intent_section}

请以 JSON 格式输出本章大纲，包含：

1. chapter_title：章节标题
2. scenes：场景列表，每个场景包含：
   - scene：场景序号
   - location：地点
   - characters：涉及角色
   - events：事件描述
   - emotional_tone：情感基调
3. key_dialogues：关键对话提示（2-3句）
4. foreshadowing_to_use：本章可以呼应的伏笔
5. foreshadowing_to_plant：本章可以新埋的伏笔
6. chapter_hook：章末钩子/悬念

注意：
- 大纲要推进主线剧情，不能原地踏步
- 场景数量控制在 2-4 个
- 章末必须有钩子，吸引读者继续看
"""

    AGENT3_AUTHOR_INTENT_SECTION = """
【作者意图】
作者希望本章写：{author_intent}
请根据作者意图生成详细大纲，确保与当前剧情衔接自然。
"""

    AGENT3_AI_SUGGESTION_PROMPT = """
你是小说剧情顾问。当前小说进度如下：

书名：{title}
当前进度：第{chapter_number}章
最近3章摘要：
{recent_summaries}

请给出 2-3 个下一章的剧情方向建议，每个包含：
1. 方向标题（一句话）
2. 简要描述（2-3句话）
3. 涉及的角色
4. 可能的冲突/看点

以 JSON 数组格式输出。
"""

    # ========== Agent 4：写作助手 ==========

    AGENT4_CHAPTER_WRITE_PROMPT = """
你是一位小说作家。请根据以下信息，撰写本章正文。

{context}

【写作要求】
1. 每章约 5000 字（4000-6000 字浮动）
2. 按场景分段，场景间用空行分隔
3. 对话用引号（""），对话前加说话人
4. 章末留悬念或转折
5. 保持与前文的衔接感，不要重复前文信息
6. 描写要具体，避免空洞的形容词堆砌

{style_constraints}

【本章大纲】
{outline}

{author_note_section}

请直接输出正文内容，不要输出大纲或其他说明文字。
"""

    AGENT4_STYLE_CONSTRAINTS_SECTION = """
【风格约束】
{style_guide}
"""

    AGENT4_AUTHOR_NOTE_SECTION = """
【作者特别交代】
{author_note}
请在写作中参考以上要求。
"""

    # ========== Agent 5：归档助手 ==========

    AGENT5_ARCHIVE_PROMPT = """
你是一位小说编辑助手。请分析本章内容，提取需要更新到知识库的信息。

【当前角色列表】
{existing_characters}

【当前活跃伏笔】
{active_foreshadowing}

【本章内容】
{chapter_content}

请以 JSON 格式输出，包含：

1. summary：本章摘要（150字以内，覆盖主要事件和转折）
2. word_count：实际字数
3. character_updates：角色状态更新列表
   - name：角色名
   - action：update（更新已有角色）或 create（新角色）
   - updates：更新内容
     - current_location：本章结束时的位置
     - current_status：本章结束时的状态
     - relationship_changes：关系变化（如有）
     - new_details：本章新发现的角色细节（如有）
4. new_entities：新出现的实体列表
   - type：character / location / skill
   - name：名称
   - details：详细信息
5. foreshadowing_updates：伏笔更新列表
   - action：plant（新埋伏笔）/ resolve（揭示伏笔）/ mention（呼应伏笔）
   - foreshadowing_id：如果是 resolve/mention，填现有伏笔ID
   - surface：如果是新埋的伏笔，填表面信息
   - hidden_truth：隐藏真相
   - category：character/plot/setting/emotion
   - keywords：检索关键词列表
   - related_characters：涉及角色列表
   - importance：重要度 1-5

注意：
- 摘要要精炼，只保留对后续剧情有影响的信息
- 角色状态要准确反映本章结束时的情况
- 伏笔检测要仔细，不要遗漏也不要误报
"""

    # ========== Agent 6：审查助手 ==========

    AGENT6_REVIEW_PROMPT = """
你是一位小说连贯性审查专家。请检查以下小说内容的一致性问题。

【小说信息】
书名：{title}
总章节数：{total_chapters}

【全书章节摘要】
{all_summaries}

【角色表】
{all_characters}

【伏笔表】
{all_foreshadowing}

请检查以下方面并以 JSON 格式输出报告：

1. 角色一致性：
   - 名字拼写是否前后一致
   - 外貌描述是否有矛盾
   - 技能/能力是否前后一致
   - 性格是否突变（无铺垫的情况下）

2. 时间线：
   - 事件顺序是否合理
   - "X天前"等时间描述是否与实际章节吻合
   - 角色位置变化是否合理

3. 伏笔：
   - 是否有遗忘的伏笔（埋了但超过30章未提及且未解决）
   - 已揭示的伏笔是否有逻辑漏洞

4. 设定一致性：
   - 世界观规则是否被违反
   - 新设定是否与已有设定矛盾

输出格式：
{
  "issues": [
    {
      "type": "character_inconsistency / timeline_error / forgotten_foreshadowing / plot_hole / setting_violation",
      "severity": "high / medium / low",
      "description": "问题描述",
      "chapters": [涉及的章节号],
      "suggestion": "修改建议"
    }
  ],
  "summary": "总结：发现X个问题，Y个高优先级"
}
"""

    # ========== 通用辅助 Prompt ==========

    CHAPTER_SUMMARY_COMPRESS_PROMPT = """
请将以下章节摘要压缩为一段连贯的概要，保留关键事件和转折，去除细节描述。

【原始摘要】
{summaries}

要求：
- 压缩到 {target_words} 字以内
- 保留每章的核心事件
- 保持时间顺序
- 不要丢失重要的剧情转折
"""
