<script setup lang="ts">
defineProps<{
	cam: {
		connection_type: 'hardware' | 'network'
	}
}>()
</script>

<template>
	<div class="px-1.5 py-0.5 text-xs font-medium rounded-sm ml-2" :class="{ 'bg-emerald-600/60': cam.connection_type == 'hardware', 'bg-cyan-600/60': cam.connection_type == 'network' }">
		{{ cam.connection_type === 'hardware' ? 'Hardware' : 'Network' }}
	</div>
</template>