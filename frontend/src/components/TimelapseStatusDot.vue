<script setup lang="ts">
import type { TimelapseStatus } from '@/types';

defineProps<{
	status: TimelapseStatus
}>()

type StatusMeta = {
	label: string,
	class: string,
}

const meta: Record<TimelapseStatus, StatusMeta> = {
	pending: { label: 'Pending', class: 'bg-zinc-400' },
	running: { label: 'Running', class: 'bg-emerald-400' },
	paused: { label: 'Paused', class: 'bg-amber-400' },
	completed: { label: 'Completed', class: 'bg-sky-400' },
}
</script>

<template>
	<span class="flex items-center gap-1.5">
		<span class="inline-block size-2 rounded-full" :class="meta[status].class" />
		{{ meta[status].label }}
	</span>
</template>