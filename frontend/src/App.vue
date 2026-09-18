<script setup lang="ts">
import { onMounted } from 'vue'
import AppLayout from './components/AppLayout.vue'
import InitPage from './views/InitPage.vue'
import { refreshSession, sessionState } from './session'

onMounted(refreshSession)
</script>

<template>
  <div v-if="sessionState.loading" class="app-loading">正在加载系统…</div>
  <InitPage v-else-if="!sessionState.ready" />
  <AppLayout v-else />
</template>

