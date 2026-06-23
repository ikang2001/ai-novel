"""小说相关 Prompt 模板"""


class NovelPromptConstant:
    """小说生成 Prompt 常量"""

    # ========== Agent 0：创意孵化助手 ==========

    AGENT0_IDEA_ENHANCE_PROMPT = """
你是一位资深网文小说策划编辑，擅长把作者的模糊点子打磨成可以支撑长篇连载的“核心创意方案”。

【作者原始想法】
{raw_idea}

【题材】
{genre}

【目标读者】
{target_readers}

【作者额外要求】
{requirements}

请在保留作者原始兴奋点的基础上完善创意，但注意：
1. 如果作者提到“类似某作品”，只提炼类型结构和爽点，不要复制已有作品的专有名词、组织、地图、角色或核心设定。
2. 必须把创意打磨成可以进入后续“世界观设定、角色设定、卷纲生成”的输入。
3. 不要只写漂亮宣传语，要补齐规则、限制、成长路径、冲突来源和长线悬念。
4. 主角能力必须有代价、边界、升级条件和反制方式，避免一开始无敌。
5. 如果作者原始想法已经是一版完整方案，说明用户正在二次修改；请优先保留上一版有效内容，只按作者额外要求定向迭代，不要完全推翻重写。
6. 输出必须是 JSON，不要输出 Markdown，不要输出解释性废话。

请输出 JSON，字段如下：
{
  "logline": "一句话卖点，30-60字",
  "enhancedCoreIdea": "完整核心创意，4000-5000字，可以直接粘贴到小说创建表单",
  "titleSuggestions": ["书名建议1", "书名建议2", "书名建议3"],
  "genrePositioning": "题材定位与读者期待",
  "protagonistDesign": {
    "identity": "主角初始身份",
    "desire": "主角核心欲望",
    "flaw": "主角缺陷",
    "growthArc": "成长弧线"
  },
  "powerSystem": {
    "name": "能力/体系名称",
    "coreRule": "核心规则",
    "upgradePath": ["阶段1", "阶段2", "阶段3", "阶段4"],
    "costAndLimit": ["代价或限制1", "代价或限制2", "代价或限制3"],
    "counterplay": ["敌人可反制方式1", "敌人可反制方式2"]
  },
  "worldRules": ["世界规则1", "世界规则2", "世界规则3"],
  "mainConflicts": ["主线冲突1", "主线冲突2", "主线冲突3"],
  "longTermHooks": ["长线悬念1", "长线悬念2", "长线悬念3"],
  "openingHook": "前三章开局钩子",
  "risksAndFixes": [
    {"risk": "可能写崩的问题", "fix": "规避方案"}
  ]
}
"""

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

请以 JSON 格式输出本章备忘录（兼容章节大纲），包含：

1. chapter_title：章节标题（不要包含"第X章"前缀，系统会自动添加）
2. chapter_task：本章核心任务（一句话，必须推动剧情状态变化）
3. reader_expectation：读者此刻最想看到什么被推进/兑现
4. previous_emotional_residue：上一章残留的情绪或局面，本章开头必须承接
5. information_gap：本章要制造或延续的信息差
6. required_ending_change：本章结尾相对开头必须发生的变化
7. scenes：场景列表，每个场景包含：
   - scene：场景序号
   - location：地点
   - characters：涉及角色
   - events：事件描述
   - emotional_tone：情感基调
   - entry_image：场景进入时的可视画面
   - exit_image：场景结束时的可视画面
   - information_gap：该场景让读者追问的问题
   - purpose：该场景改变了什么
8. character_motivations：角色动机链列表
   - character：角色名
   - current_interest：当前利益/目标
   - pressure：当前压力
   - expected_action：合理行动
   - constraint：不能这么做的限制
9. key_dialogues：关键对话提示（2-3句）
10. hook_operations：本章伏笔操作列表
   - action：open/advance/resolve/defer/plant
   - foreshadowing_id：已有伏笔ID（如有）
   - surface：读者看到的表面信息
   - reason：为什么本章要处理
11. foreshadowing_to_use：本章可以呼应的伏笔
12. foreshadowing_to_plant：本章可以新埋的伏笔
13. chapter_hook：章末钩子/悬念
14. prohibitions：本章禁止事项列表

注意：
- 大纲要推进主线剧情，不能原地踏步
- 场景数量控制在 2-4 个
- 章末必须有钩子，吸引读者继续看
- 角色行动必须来自性格、当前利益和上一章局面，不能为了剧情突然转向
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
1. 每章约 8000 字（8000-10000 字浮动）
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
不要在正文开头输出"第X章"或章节标题，系统会自动添加。
"""

    AGENT4_GOVERNED_CHAPTER_WRITE_PROMPT = """
你是一位长篇小说作者。你只根据下面的九层写作提示词写正文，不要额外发明与硬事实冲突的设定。

{context_layers}

{author_note_section}

【输出要求】
1. 直接输出正文，不要输出标题、大纲、分析、解释或 Markdown 代码块。
2. 正文约 4000-6000 字，允许根据场景密度自然浮动。
3. 开头必须接住上一章的画面、情绪或行动，不要复述前情。
4. 每个场景都要有可见动作、具体物件、对话或环境变化，不能只写心理总结。
5. 所有伏笔推进必须能在正文中定位到具体场景；单纯内心一提不算推进。
6. 避免 AI 腔：不要堆叠空泛形容词，不要频繁使用"他知道/他明白/这一刻"，不要用宏大总结替代事件。
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
3. ending_state：本章结尾状态
   - final_image：最后一个可视画面
   - location：结尾地点
   - emotional_residue：留给下一章的情绪残留
   - open_conflict：尚未解决的冲突
   - reader_expectation：读者下一章最期待什么
   - character_states：结尾角色状态列表
4. reader_expectation：下一章读者期待（一句话）
5. character_updates：角色状态更新列表
   - name：角色名
   - action：update（更新已有角色）或 create（新角色）
   - updates：更新内容
     - current_location：本章结束时的位置
     - current_status：本章结束时的状态
     - relationship_changes：关系变化（如有）
     - new_details：本章新发现的角色细节（如有）
6. new_entities：新出现的实体列表
   - type：character / location / skill
   - name：名称
   - details：详细信息
7. foreshadowing_updates：伏笔更新列表
   - action：plant（新埋伏笔）/ resolve（揭示伏笔）/ mention（呼应伏笔）/ advance（推进伏笔）/ defer（明确暂缓）
   - foreshadowing_id：如果是 resolve/mention，填现有伏笔ID
   - surface：如果是新埋的伏笔，填表面信息
   - hidden_truth：隐藏真相
   - category：character/plot/setting/emotion
   - keywords：检索关键词列表
   - related_characters：涉及角色列表
   - importance：重要度 1-5
   - lifecycle_stage：planted/open/progressing/near_payoff/pressured
   - note：本章如何处理该伏笔
8. timeline_events：时间线事件列表
9. style_memory_updates：可以学习的用户偏好或反 AI 腔改法

注意：
- 摘要要精炼，只保留对后续剧情有影响的信息
- 角色状态要准确反映本章结束时的情况
- 伏笔检测要仔细，不要遗漏也不要误报
- ending_state 必须服务于下一章上下文衔接
"""

    AGENT4_DRAFT_AUDIT_PROMPT = """
你是一位严苛的长篇小说审稿人。请只审查本章草稿是否符合上下文包和章节备忘录，不要重写正文。

【上下文包】
{context_package}

【章节草稿】
{draft_content}

请检查：
1. 是否自然承接上一章结尾画面、情绪和行动。
2. 角色行为是否符合过往经历、当前利益、性格和压力。
3. 本章 memo 的 chapter_task、reader_expectation、required_ending_change 是否有正文痕迹。
4. hook_operations 和 hookDebt 是否被具体场景推进。
5. 是否出现设定冲突、时间线冲突、信息边界错误。
6. 是否有 AI 腔：空泛总结、重复句式、同质段落、只解释不演示。
7. 场景之间是否跳跃突兀，是否缺少转场。

定位要求：每个 issue 都必须尽量给出 paragraphIndex 和 evidenceText；evidenceText 必须直接摘自章节草稿，方便前端定位到正文段落。

请以 JSON 输出：
{
  "issues": [
    {
      "type": "continuity / character_ooc / hook_drift / memo_drift / pacing / ai_tone / setting_conflict",
      "severity": "high / medium / low",
      "description": "具体问题",
      "chapters": [章节号],
      "paragraphIndex": 3,
      "evidenceText": "正文中能定位问题的原句或短段，必须来自草稿",
      "startOffset": 120,
      "endOffset": 180,
      "suggestion": "具体修订建议"
    }
  ],
  "summary": "审稿总结",
  "should_revise": true,
  "revision_brief": "给修订者的简洁修订指令"
}
"""

    AGENT4_DRAFT_REVISION_PROMPT = """
你是一位小说修订编辑。请根据审稿报告修订章节草稿。

【上下文包】
{context_package}

【审稿报告】
{audit_report}

【原始草稿】
{draft_content}

修订要求：
1. 保留原章节的主要剧情和信息，不要重写成另一章。
2. 优先修复 high/medium 问题。
3. 补强上一章衔接、角色动机、伏笔推进和场景转场。
4. 去掉 AI 腔和空泛总结，用具体动作、物件、对话、环境变化替代。
5. 直接输出修订后的正文，不要输出解释。
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
