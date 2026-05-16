"""标题生成智能体适配器"""

from app.schemas.article import ArticleState


class TitleGeneratorAgent:
    """标题生成智能体"""

    async def run(self, service, state: ArticleState):
        await service.agent1_generate_title_options(state)

# 这就特别适合新手理解。
# 它的人话非常简单：
# “标题 agent 自己不直接写逻辑，它只是转手调用 service.agent1_generate_title_options(state)。”
# 所以你现在应该明白一件事：
# 这个项目不是每一层都做复杂事情，有些层是为了“结构清晰”存在的。

# async_service：负责阶段任务
# agent_service：负责阶段入口和错误包装
# orchestrator：负责编排步骤
# agent：负责把某个角色转给具体方法
# 真正调用模型的逻辑：还在更下面
# 也就是说，下一站终于要到“真正生成标题”的地方了：