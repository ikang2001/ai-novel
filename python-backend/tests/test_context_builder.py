import unittest

from app.services.context_builder import ContextBuilder


class FakeNovelService:
    def __init__(self):
        self.chapters = [
            {"id": 1, "novelId": 9, "chapterNumber": 1, "title": "一", "content": "第一章正文结尾A", "summary": "第一章摘要", "status": "confirmed", "endingState": {"readerExpectation": "继续追问A"}},
            {"id": 2, "novelId": 9, "chapterNumber": 2, "title": "二", "content": "第二章旧稿不应进入上下文", "summary": "第二章旧摘要", "status": "draft", "endingState": {}},
            {"id": 3, "novelId": 9, "chapterNumber": 3, "title": "三", "content": "第三章未来稿", "summary": "第三章摘要", "status": "draft", "endingState": {}},
        ]

    async def get_novel(self, novel_id):
        return {
            "id": novel_id,
            "title": "测试书",
            "genre": "xuanyi",
            "targetReaders": "general",
            "currentChapterNumber": 3,
            "currentVolumeNumber": 1,
            "worldSetting": {},
            "volumeOutline": [],
            "styleGuide": {},
            "synopsis": "",
        }

    async def get_next_chapter_number(self, novel_id):
        return 4

    async def get_recent_chapters_before(self, novel_id, chapter_number, limit=3):
        rows = [c for c in self.chapters if c["chapterNumber"] < chapter_number]
        return rows[-limit:]

    async def get_previous_chapter(self, novel_id, chapter_number):
        rows = [c for c in self.chapters if c["chapterNumber"] < chapter_number]
        return rows[-1] if rows else None

    async def get_novel_state(self, novel_id, state_type):
        return None


class FakeCharacterService:
    async def get_core_characters(self, novel_id):
        return []

    async def get_all_current_states(self, novel_id):
        return []

    async def get_all_characters(self, novel_id):
        return []

    async def find_by_name(self, novel_id, name):
        return None


class FakeForeshadowingService:
    async def get_hook_debt(self, novel_id, target_number, limit=8):
        return []

    async def get_active_foreshadowing(self, novel_id):
        return []

    async def search_by_keywords(self, novel_id, keywords):
        return []

    async def get_stale_foreshadowing(self, novel_id, chapter_number, threshold=20):
        return []

    async def get_near_target_foreshadowing(self, novel_id, chapter_number):
        return []


class ContextBuilderTest(unittest.IsolatedAsyncioTestCase):
    async def test_context_package_excludes_current_chapter_old_draft(self):
        builder = ContextBuilder(FakeNovelService(), FakeCharacterService(), FakeForeshadowingService())

        package = await builder.build_package(
            novel_id=9,
            chapter_outline={"chapterTask": "重写第二章"},
            chapter_id=2,
            chapter_number=2,
        )

        self.assertEqual(package["trace"]["excludedChapterNumber"], 2)
        self.assertEqual(package["trace"]["recentChapterNumbers"], [1])
        self.assertEqual(package["trace"]["previousChapterNumber"], 1)
        self.assertIn("第一章正文结尾A", package["recentMemory"]["previousChapter"]["tail"])
        self.assertNotIn("第二章旧稿", str(package))


if __name__ == "__main__":
    unittest.main()
