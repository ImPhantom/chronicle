<script setup lang="ts">
import AppNavbar from '@/components/AppNavbar.vue'
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <AppNavbar />
    <main class="flex-1 container mx-auto px-4 py-6">
      <RouterView />
    </main>
  </div>
</template>

