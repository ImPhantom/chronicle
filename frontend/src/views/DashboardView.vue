<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { CameraResponse, TimelapseResponse, TimelapseStatus } from '@/types'
import TimelapseDialog from '@/components/TimelapseDialog.vue';
import { PhCamera, PhCameraSlash, PhFilmStrip, PhTimer, PhVideoCamera } from '@phosphor-icons/vue';
import ConnectionTypeBadge from '@/components/ConnectionTypeBadge.vue';
import { getTimelapses } from '@/api/timelapse';
import { getCameras } from '@/api/camera';

const cameras = ref<CameraResponse[]>([])
const timelapses = ref<TimelapseResponse[]>([])

const fetchData = async () => {
	try {
		const [tls, cams] = await Promise.all([
			getTimelapses(),
			getCameras(),
		])
		timelapses.value = tls
		cameras.value = cams
	} catch {
		timelapses.value = []
		cameras.value = []
	}
}

onMounted(async () => {
	await fetchData()
})

const statusMeta: Record<TimelapseStatus | 'scheduled', { dot: string; pill: string; label: string }> = {
	pending: { dot: 'bg-zinc-400', pill: 'bg-zinc-700/70 text-zinc-300', label: 'Pending' },
	scheduled: { dot: 'bg-indigo-400', pill: 'bg-indigo-950/70 text-indigo-300', label: 'Scheduled' },
	running: { dot: 'bg-emerald-400', pill: 'bg-emerald-950/70 text-emerald-300', label: 'Running' },
	paused: { dot: 'bg-amber-400', pill: 'bg-amber-950/70 text-amber-300', label: 'Paused' },
	completed: { dot: 'bg-sky-400', pill: 'bg-sky-950/70 text-sky-300', label: 'Completed' },
}

function statusKey(tl: TimelapseResponse): TimelapseStatus | 'scheduled' {
	if (tl.status === 'pending' && tl.started_at && new Date(tl.started_at) > new Date()) return 'scheduled'
	return tl.status
}

function formatInterval(seconds: number): string {
	if (seconds < 60) return `Every ${seconds}s`
	if (seconds < 3600) return `Every ${Math.round(seconds / 60)}m`
	const h = Math.floor(seconds / 3600)
	const m = Math.round((seconds % 3600) / 60)
	return m > 0 ? `Every ${h}h ${m}m` : `Every ${h}h`
}
</script>

<template>
	<div>
		<div class="flex items-center justify-between mb-6">
			<h1 class="text-2xl font-semibold">Active Timelapses</h1>
			<TimelapseDialog v-on:timelapse-created="fetchData" />
		</div>

		<div v-if="timelapses.length === 0" class="flex flex-col items-center justify-center py-24 text-muted-foreground gap-3">
			<PhVideoCamera :size="56" class="text-zinc-600" />
			<p class="text-base font-medium text-zinc-400">No timelapses yet</p>
			<p class="text-sm">Add a camera from the navbar to get started.</p>
		</div>

		<div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
			<a 
				v-for="timelapse in timelapses" :key="timelapse.id"
				:href="`/timelapse/${timelapse.id}`"
				class="flex flex-col border border-zinc-300/60 dark:border-zinc-800 rounded-xl overflow-hidden bg-zinc-100 dark:bg-zinc-900 hover:cursor-pointer hover:-translate-y-1 hover:shadow-lg hover:shadow-zinc-400/50 dark:hover:shadow-black/40 transition-all duration-200"
			>
				<!-- Thumbnail -->
				<div class="relative aspect-video w-full bg-zinc-500 dark:bg-zinc-800/60">
					<!-- Fallback icon -->
					<PhCameraSlash variant="duotone" :size="64" class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-red-400/40" />
					<!-- Last frame image -->
					<img v-if="timelapse.last_frame_id" :src="`/api/v1/frames/${timelapse.last_frame_id}/image`" class="absolute inset-0 w-full h-full object-cover" @error="(e) => ((e.currentTarget as HTMLImageElement).style.display = 'none')" />
					<!-- Bottom gradient for legibility -->
					<div class="absolute bottom-0 left-0 right-0 h-12 bg-linear-to-t from-zinc-800/60 dark:from-black/70 to-transparent pointer-events-none" />
					<!-- Frame count (bottom-left) -->
					<div v-if="timelapse.frame_count > 0" class="absolute bottom-2 left-2.5 flex items-center gap-1 text-xs text-white/80">
						<PhFilmStrip :size="14" />
						<span>{{ timelapse.frame_count.toLocaleString() }}</span>
					</div>
					<!-- Status pill (top-right) -->
					<div class="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium backdrop-blur-sm" :class="statusMeta[statusKey(timelapse)].pill">
						<span class="inline-block w-1.5 h-1.5 rounded-full" :class="statusMeta[statusKey(timelapse)].dot" />
						{{ statusMeta[statusKey(timelapse)].label }}
					</div>
				</div>

				<!-- Card body -->
				<div class="flex flex-col gap-2 p-3.5">
					<h2 class="text-base font-medium truncate">{{ timelapse.name }}</h2>
					<div class="flex items-center gap-1.5 text-sm text-muted-foreground">
						<PhCamera variant="duotone" :size="16" class="text-zinc-400 shrink-0" />
						<span class="truncate">{{cameras.find(c => c.id === timelapse.camera_id)?.name || 'Unknown Camera'}}</span>
						<ConnectionTypeBadge :cam="cameras.find(c => c.id === timelapse.camera_id) || { connection_type: 'network' }" />
					</div>
					<div class="flex items-center gap-1.5 text-sm text-muted-foreground">
						<PhTimer variant="duotone" :size="16" class="text-zinc-400 shrink-0" />
						<span>{{ formatInterval(timelapse.interval_seconds) }}</span>
					</div>
				</div>
			</a>
		</div>
	</div>
</template>
