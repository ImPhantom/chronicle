<script setup lang="ts">
import type { Component } from 'vue';

defineProps<{
	icon?: Component,
	label: string,
}>()
</script>

<template>
	<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-zinc-100 dark:bg-zinc-700/80 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-600">
		<component v-if="icon" :is="icon" size="12" class="shrink-0" />
		{{ label }}
	</span>
</template>