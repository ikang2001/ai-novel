/**
 * 小说工作区状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getNovel, listChapters, listCharacters, listForeshadowing } from '@/api/novelController'

export const useNovelStore = defineStore('novel', () => {
  const currentNovel = ref<API.NovelVO | null>(null)
  const chapters = ref<API.ChapterVO[]>([])
  const characters = ref<API.CharacterVO[]>([])
  const foreshadowing = ref<API.ForeshadowingVO[]>([])
  const activeChapterId = ref<number | null>(null)
  const isGenerating = ref(false)

  async function fetchNovel(id: number) {
    const res = await getNovel({ novelId: id })
    if (res.data.code === 0 && res.data.data) {
      currentNovel.value = res.data.data
    }
  }

  async function fetchChapters(novelId: number) {
    const res = await listChapters(novelId)
    if (res.data.code === 0 && res.data.data) {
      chapters.value = res.data.data
    }
  }

  async function fetchCharacters(novelId: number) {
    const res = await listCharacters(novelId)
    if (res.data.code === 0 && res.data.data) {
      characters.value = res.data.data
    }
  }

  async function fetchForeshadowing(novelId: number) {
    const res = await listForeshadowing(novelId)
    if (res.data.code === 0 && res.data.data) {
      foreshadowing.value = res.data.data
    }
  }

  function setActiveChapter(id: number | null) {
    activeChapterId.value = id
  }

  function reset() {
    currentNovel.value = null
    chapters.value = []
    characters.value = []
    foreshadowing.value = []
    activeChapterId.value = null
    isGenerating.value = false
  }

  return {
    currentNovel,
    chapters,
    characters,
    foreshadowing,
    activeChapterId,
    isGenerating,
    fetchNovel,
    fetchChapters,
    fetchCharacters,
    fetchForeshadowing,
    setActiveChapter,
    reset,
  }
})
