<template>
  <a-drawer
    :open="visible"
    @update:open="$emit('update:visible', $event)"
    title="角色管理"
    width="480"
    placement="right"
  >
    <div class="character-panel">
      <a-button type="primary" block @click="showCreate = true" style="margin-bottom: 16px">
        <template #icon><PlusOutlined /></template>
        添加角色
      </a-button>

      <a-collapse v-if="characters.length" :bordered="false">
        <a-collapse-panel v-for="char in characters" :key="char.id" :header="char.name">
          <template #extra>
            <a-tag :color="ROLE_TYPE_COLOR_MAP[char.roleType || '']" size="small">
              {{ ROLE_TYPE_TEXT_MAP[char.roleType || ''] || char.roleType }}
            </a-tag>
          </template>
          <div class="char-detail">
            <p v-if="char.appearance"><strong>外貌：</strong>{{ char.appearance }}</p>
            <p v-if="char.personality"><strong>性格：</strong>{{ char.personality }}</p>
            <p v-if="char.currentLocation"><strong>位置：</strong>{{ char.currentLocation }}</p>
            <p v-if="char.currentStatus"><strong>状态：</strong>{{ char.currentStatus }}</p>
            <p v-if="char.notes"><strong>备注：</strong>{{ char.notes }}</p>
          </div>
          <div class="char-actions">
            <a-button size="small" @click="handleEdit(char)">编辑</a-button>
            <a-popconfirm title="确定删除?" @confirm="handleDelete(char.id!)">
              <a-button size="small" danger>删除</a-button>
            </a-popconfirm>
          </div>
        </a-collapse-panel>
      </a-collapse>

      <a-empty v-else description="暂无角色" />
    </div>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:open="showCreate"
      :title="editingId ? '编辑角色' : '添加角色'"
      @ok="handleSubmit"
      :confirm-loading="submitting"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="角色名" required>
          <a-input v-model:value="form.name" placeholder="角色名" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="form.roleType" placeholder="选择类型">
            <a-select-option v-for="(label, key) in ROLE_TYPE_TEXT_MAP" :key="key" :value="key">
              {{ label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="外貌">
          <a-textarea v-model:value="form.appearance" :rows="2" />
        </a-form-item>
        <a-form-item label="性格">
          <a-textarea v-model:value="form.personality" :rows="2" />
        </a-form-item>
        <a-form-item label="背景">
          <a-textarea v-model:value="form.background" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { listCharacters, createCharacter, updateCharacter, deleteCharacter } from '@/api/novelController'
import { ROLE_TYPE_TEXT_MAP, ROLE_TYPE_COLOR_MAP } from '@/constants/novel'

const props = defineProps<{ visible: boolean; novelId: number }>()
const emit = defineEmits(['update:visible', 'refresh'])

const characters = ref<API.CharacterVO[]>([])
const showCreate = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)

const form = reactive({
  name: '',
  roleType: undefined as string | undefined,
  appearance: '',
  personality: '',
  background: '',
})

const loadCharacters = async () => {
  const res = await listCharacters(props.novelId)
  if (res.data.code === 0) characters.value = res.data.data || []
}

watch(() => props.visible, (v) => { if (v) loadCharacters() })

const resetForm = () => {
  form.name = ''
  form.roleType = undefined
  form.appearance = ''
  form.personality = ''
  form.background = ''
  editingId.value = null
}

const handleEdit = (char: API.CharacterVO) => {
  editingId.value = char.id!
  form.name = char.name || ''
  form.roleType = char.roleType
  form.appearance = char.appearance || ''
  form.personality = char.personality || ''
  form.background = char.background || ''
  showCreate.value = true
}

const handleSubmit = async () => {
  if (!form.name?.trim()) {
    message.warning('请输入角色名')
    return
  }
  submitting.value = true
  try {
    if (editingId.value) {
      await updateCharacter(editingId.value, { ...form })
      message.success('更新成功')
    } else {
      await createCharacter(props.novelId, { ...form })
      message.success('创建成功')
    }
    showCreate.value = false
    resetForm()
    loadCharacters()
    emit('refresh')
  } catch (e) {
    message.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  try {
    await deleteCharacter(id)
    message.success('删除成功')
    loadCharacters()
    emit('refresh')
  } catch (e) {
    message.error('删除失败')
  }
}
</script>

<style scoped>
.char-detail p {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.6;
}

.char-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
</style>
