<script setup lang="ts">
defineProps<{ title: string }>()
</script>

<template>
  <div>
    <div class="page-heading"><div><div class="eyebrow dark">COMING NEXT</div><h1>{{ title }}</h1><p>该模块将在下一阶段接入。</p></div></div>
    <section class="content-card placeholder"><div class="placeholder-mark">V</div><h2>基础骨架已就绪</h2><p>当前优先打通反馈录入与数据存储。</p></section>
  </div>
</template>

