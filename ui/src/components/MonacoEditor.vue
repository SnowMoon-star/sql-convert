<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { VueMonacoEditor } from '@guolao/vue-monaco-editor';
import { useThemeStore } from '../store/theme';

const props = defineProps({
  value: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'sql'
  },
  readOnly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:value']);
const isFocused = ref(false);
const editorRef = ref<any>(null);
const themeStore = useThemeStore();

// 根据主题动态切换 Monaco Editor 主题
const editorTheme = computed(() => themeStore.isDark ? 'vs-dark' : 'vs');

const handleUpdate = (val: string | undefined) => {
  emit('update:value', val || '');
};

const handleEditorMount = (editorInstance: any) => {
  editorRef.value = editorInstance;
  editorInstance.onDidFocusEditorWidget(() => {
    isFocused.value = true;
  });
  editorInstance.onDidBlurEditorWidget(() => {
    isFocused.value = false;
  });
};

// 监听 readOnly 的变化动态更新编辑器的 option
watch(() => props.readOnly, (newVal) => {
  if (editorRef.value) {
    editorRef.value.updateOptions({ readOnly: newVal });
  }
});

// 主题变化时更新编辑器实例的主题
watch(() => themeStore.isDark, () => {
  if (editorRef.value) {
    editorRef.value.updateOptions({ theme: editorTheme.value });
  }
});

const editorOptions = ref({
  selectOnLineNumbers: true,
  roundedSelection: false,
  readOnly: props.readOnly,
  cursorStyle: 'line',
  automaticLayout: true,
  fontSize: 13,
  fontFamily: "Fira Code, Menlo, Monaco, Consolas, monospace",
  minimap: {
    enabled: false
  },
  scrollbar: {
    vertical: 'auto',
    horizontal: 'auto',
    verticalScrollbarSize: 8,
    horizontalScrollbarSize: 8
  },
  lineNumbersMinChars: 3,
});
</script>

<template>
  <div 
    class="w-full h-full border rounded-lg overflow-hidden transition-all duration-300"
    :class="[
      isFocused ? 'border-indigo-500/70 shadow-lg shadow-indigo-500/10' : '',
    ]"
    :style="{ background: 'var(--bg-secondary)', borderColor: isFocused ? '' : 'var(--border-color)' }"
  >
    <VueMonacoEditor
      :value="props.value"
      @update:value="handleUpdate"
      @mount="handleEditorMount"
      :language="props.language"
      :theme="editorTheme"
      :options="editorOptions"
    />
  </div>
</template>
