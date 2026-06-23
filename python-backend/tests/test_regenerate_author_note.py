import unittest
from types import SimpleNamespace

from app.models.novel_enums import ChapterStatusEnum
from app.routers.novel import regenerate_chapter
from app.schemas.novel import ChapterRegenerateRequest


class FakeNovelService:
    async def get_chapter(self, chapter_id: int):
        return {
            "id": chapter_id,
            "novelId": 7,
            "chapterNumber": 3,
            "outline": '{"chapterTitle": "测试章节"}',
            "status": ChapterStatusEnum.DRAFT.value,
        }

    async def get_novel(self, novel_id: int):
        return {"id": novel_id, "userId": 1}


class FakeAsyncService:
    def __init__(self):
        self.last_payload = None

    async def start_chapter_generation(self, **kwargs):
        self.last_payload = kwargs
        return "task-1"


class RegenerateAuthorNoteTest(unittest.IsolatedAsyncioTestCase):
    async def test_regenerate_without_body_keeps_compatibility(self):
        async_service = FakeAsyncService()
        services = {"novel_service": FakeNovelService(), "async_service": async_service}
        current_user = SimpleNamespace(id=1, user_role="user")

        result = await regenerate_chapter(11, None, current_user, services)

        self.assertEqual(result["data"]["taskId"], "task-1")
        self.assertIsNone(async_service.last_payload["author_note"])

    async def test_regenerate_with_author_note_passes_to_generation(self):
        async_service = FakeAsyncService()
        services = {"novel_service": FakeNovelService(), "async_service": async_service}
        current_user = SimpleNamespace(id=1, user_role="user")
        request = ChapterRegenerateRequest(authorNote="本章多写动作，不要提前揭露真相")

        await regenerate_chapter(12, request, current_user, services)

        self.assertEqual(async_service.last_payload["author_note"], "本章多写动作，不要提前揭露真相")


if __name__ == "__main__":
    unittest.main()
