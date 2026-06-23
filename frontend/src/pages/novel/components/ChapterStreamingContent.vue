<template>
  <div class="streaming-content" ref="contentRef" @scroll="handleScroll">
    <div v-if="chapterTitle" class="chapter-title">{{ chapterTitle }}</div>
    <div class="markdown-body" v-html="renderedContent"></div>
    <span v-if="isStreaming" class="typing-cursor">|</span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { marked } from 'marked'

const props = defineProps<{
  content: string
  isStreaming: boolean
  chapterTitle?: string
}>()

const contentRef = ref<HTMLElement | null>(null)
const shouldAutoScroll = ref(true)

const renderedContent = computed(() => {
  if (!props.content) return ''
  return marked(props.content) as string
})

watch(
  () => props.content,
  async () => {
    await nextTick()
    if (contentRef.value && shouldAutoScroll.value) {
      contentRef.value.scrollTop = contentRef.value.scrollHeight
    }
  }
)

const handleScroll = () => {
  const el = contentRef.value
  if (!el) return
  shouldAutoScroll.value = el.scrollHeight - el.scrollTop - el.clientHeight < 96
}
</script>

<style scoped>
.streaming-content {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

.chapter-title {
  font-family: 'Outfit', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 24px;
  text-align: center;
}

.markdown-body {
  font-family: 'Work Sans', sans-serif;
  font-size: 15px;
  line-height: 1.8;
  color: #374151;
}

.markdown-body :deep(p) {
  margin: 0 0 16px;
  text-indent: 2em;
}

.markdown-body :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  margin: 32px 0 16px;
  color: #0F172A;
}

.markdown-body :deep(h3) {
  font-size: 17px;
  font-weight: 600;
  margin: 24px 0 12px;
}

.typing-cursor {
  display: inline-block;
  animation: blink 1s step-end infinite;
  color: #22C55E;
  font-weight: 700;
}

@keyframes blink {
  50% { opacity: 0; }
}
</style>
