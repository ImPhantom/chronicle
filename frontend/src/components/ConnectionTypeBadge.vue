<script setup lang="ts">
defineProps<{
	cam: {
		connection_type: 'hardware' | 'network'
	}
}>()

const meta: Record<'hardware' | 'network', { label: string, class: string }> = {
	hardware: { label: 'Hardware', class: 'bg-emerald-900/80 text-emerald-200' },
	network: { label: 'Network', class: 'bg-cyan-900/70 text-cyan-200' },
}
</script>

<template>
	<div class="px-1.5 py-0.5 text-xs font-medium rounded-sm" :class="meta[cam.connection_type].class">
		{{ meta[cam.connection_type].label }}
	</div>
</template>