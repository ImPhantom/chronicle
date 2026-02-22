<script setup lang="ts">
import type { TimelapseStatus } from '@/types';

defineProps<{
	status: TimelapseStatus
	scheduled?: boolean
}>()

type StatusMeta = {
	label: string,
	class: string,
}

const meta: Record<TimelapseStatus | 'scheduled', StatusMeta> = {
	pending: { label: 'Pending', class: 'bg-zinc-400' },
	scheduled: { label: 'Scheduled', class: 'bg-indigo-400' },
	running: { label: 'Running', class: 'bg-emerald-400' },
	paused: { label: 'Paused', class: 'bg-amber-400' },
	completed: { label: 'Completed', class: 'bg-sky-400' },
}
</script>

<template>
	<span class="flex items-center gap-1.5">
		<span class="inline-block size-2 rounded-full" :class="(scheduled && status === 'pending' ? meta.scheduled : meta[status]).class" />
		{{ (scheduled && status === 'pending' ? meta.scheduled : meta[status]).label }}
	</span>
</template>