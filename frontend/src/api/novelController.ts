// @ts-ignore
/* eslint-disable */
import request from '@/request'

// ========== 小说管理 ==========

/** 创建小说 POST /novel/create */
export async function createNovel(body: API.NovelCreateRequest, options?: { [key: string]: any }) {
  return request<API.BaseResponseDict>('/novel/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 获取小说详情 GET /novel/${param0} */
export async function getNovel(params: API.getNovelParams, options?: { [key: string]: any }) {
  const { novelId: param0, ...queryParams } = params
  return request<API.BaseResponseNovelVO>(`/novel/${param0}`, {
    method: 'GET',
    params: { ...queryParams },
    ...(options || {}),
  })
}

/** 小说列表 GET /novel/list */
export async function listNovel(
  params?: { page?: number; pageSize?: number },
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseDict>('/novel/list', {
    method: 'GET',
    params: params || {},
    ...(options || {}),
  })
}

/** 修改小说设定 PUT /novel/${param0}/setting */
export async function updateNovelSetting(
  novelId: number,
  body: API.NovelSettingUpdateRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseBoolean>(`/novel/${novelId}/setting`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 删除小说 DELETE /novel/${param0} */
export async function deleteNovel(novelId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseBoolean>(`/novel/${novelId}`, {
    method: 'DELETE',
    ...(options || {}),
  })
}

// ========== 风格管理 ==========

/** 风格分析 POST /novel/${param0}/style/analyze */
export async function analyzeStyle(
  novelId: number,
  body: API.StyleAnalyzeRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseDict>(`/novel/${novelId}/style/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 修改风格指南 PUT /novel/${param0}/style */
export async function updateStyle(
  novelId: number,
  body: Record<string, any>,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseBoolean>(`/novel/${novelId}/style`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

// ========== 角色管理 ==========

/** 角色列表 GET /novel/${param0}/characters */
export async function listCharacters(novelId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseListCharacterVO>(`/novel/${novelId}/characters`, {
    method: 'GET',
    ...(options || {}),
  })
}

/** 创建角色 POST /novel/${param0}/characters */
export async function createCharacter(
  novelId: number,
  body: API.CharacterCreateRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseLong>(`/novel/${novelId}/characters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 修改角色 PUT /novel/character/${param0} */
export async function updateCharacter(
  characterId: number,
  body: API.CharacterUpdateRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseBoolean>(`/novel/character/${characterId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 删除角色 DELETE /novel/character/${param0} */
export async function deleteCharacter(characterId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseBoolean>(`/novel/character/${characterId}`, {
    method: 'DELETE',
    ...(options || {}),
  })
}

// ========== 伏笔管理 ==========

/** 伏笔列表 GET /novel/${param0}/foreshadowing */
export async function listForeshadowing(
  novelId: number,
  params?: { status?: string },
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseListForeshadowingVO>(`/novel/${novelId}/foreshadowing`, {
    method: 'GET',
    params: params || {},
    ...(options || {}),
  })
}

/** 创建伏笔 POST /novel/${param0}/foreshadowing */
export async function createForeshadowing(
  novelId: number,
  body: API.ForeshadowingCreateRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseLong>(`/novel/${novelId}/foreshadowing`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 修改伏笔 PUT /novel/foreshadowing/${param0} */
export async function updateForeshadowing(
  foreshadowingId: number,
  body: API.ForeshadowingUpdateRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseBoolean>(`/novel/foreshadowing/${foreshadowingId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 揭示伏笔 PUT /novel/foreshadowing/${param0}/resolve */
export async function resolveForeshadowing(foreshadowingId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseBoolean>(`/novel/foreshadowing/${foreshadowingId}/resolve`, {
    method: 'PUT',
    ...(options || {}),
  })
}

/** 放弃伏笔 PUT /novel/foreshadowing/${param0}/abandon */
export async function abandonForeshadowing(foreshadowingId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseBoolean>(`/novel/foreshadowing/${foreshadowingId}/abandon`, {
    method: 'PUT',
    ...(options || {}),
  })
}

// ========== 章节操作 ==========

/** 规划章节大纲 POST /novel/${param0}/chapter/plan */
export async function planChapter(
  novelId: number,
  body: API.ChapterPlanRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseDict>(`/novel/${novelId}/chapter/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 生成章节内容 POST /novel/${param0}/chapter/generate */
export async function generateChapter(
  novelId: number,
  body: API.ChapterGenerateRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseDict>(`/novel/${novelId}/chapter/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 确认章节 PUT /novel/chapter/${param0}/confirm */
export async function confirmChapter(
  chapterId: number,
  body?: API.ChapterConfirmRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseDict>(`/novel/chapter/${chapterId}/confirm`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data: body || {},
    ...(options || {}),
  })
}

/** 重新生成章节 PUT /novel/chapter/${param0}/regenerate */
export async function regenerateChapter(chapterId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseDict>(`/novel/chapter/${chapterId}/regenerate`, {
    method: 'PUT',
    ...(options || {}),
  })
}

/** 手动修改章节内容 PUT /novel/chapter/${param0}/content */
export async function updateChapterContent(
  chapterId: number,
  body: API.ChapterContentUpdateRequest,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseBoolean>(`/novel/chapter/${chapterId}/content`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 删除章节 DELETE /novel/chapter/${param0} */
export async function deleteChapter(chapterId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseBoolean>(`/novel/chapter/${chapterId}`, {
    method: 'DELETE',
    ...(options || {}),
  })
}

/** 手动创建章节 POST /novel/${param0}/chapter/create */
export async function createChapter(
  novelId: number,
  body: { title?: string; chapterNumber?: number },
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseDict>(`/novel/${novelId}/chapter/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data: body,
    ...(options || {}),
  })
}

/** 修改章节标题 PUT /novel/chapter/${param0}/title */
export async function updateChapterTitle(
  chapterId: number,
  title: string,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseBoolean>(`/novel/chapter/${chapterId}/title`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data: { title },
    ...(options || {}),
  })
}

/** 章节列表 GET /novel/${param0}/chapters */
export async function listChapters(novelId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseListChapterVO>(`/novel/${novelId}/chapters`, {
    method: 'GET',
    ...(options || {}),
  })
}

/** 章节详情 GET /novel/chapter/${param0} */
export async function getChapter(params: API.getChapterParams, options?: { [key: string]: any }) {
  const { chapterId: param0, ...queryParams } = params
  return request<API.BaseResponseChapterVO>(`/novel/chapter/${param0}`, {
    method: 'GET',
    params: { ...queryParams },
    ...(options || {}),
  })
}

// ========== 审查与导出 ==========

/** 连贯性检查 POST /novel/${param0}/consistency */
export async function checkConsistency(novelId: number, options?: { [key: string]: any }) {
  return request<API.BaseResponseConsistencyReport>(`/novel/${novelId}/consistency`, {
    method: 'POST',
    ...(options || {}),
  })
}

/** 导出小说 GET /novel/${param0}/export */
export async function exportNovel(
  novelId: number,
  params?: { format?: string },
  options?: { [key: string]: any }
) {
  return request<any>(`/novel/${novelId}/export`, {
    method: 'GET',
    params: params || {},
    ...(options || {}),
  })
}
