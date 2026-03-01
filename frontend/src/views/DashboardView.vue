<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { CameraResponse, TimelapseResponse, TimelapseStatus } from '@/types'
import TimelapseDialog from '@/components/TimelapseDialog.vue';
import { PhCamera, PhCameraSlash, PhFilmStrip, PhSpinner, PhTimer, PhVideoCamera, PhWarningOctagon } from '@phosphor-icons/vue';
import ConnectionTypeBadge from '@/components/ConnectionTypeBadge.vue';
import { getTimelapses } from '@/api/timelapse';
import { getCameras } from '@/api/camera';
import BaseAlert from '@/components/BaseAlert.vue';
import { useRoute } from 'vue-router';
import { formatInterval } from '@/lib/format';

const cameras = ref<CameraResponse[]>([])
const timelapses = ref<TimelapseResponse[]>([])
const isLoading = ref(true)
const errorMessage = ref<string>('')

const route = useRoute()

const fetchData = async () => {
	isLoading.value = true
	try {
		const [tls, cams] = await Promise.all([
			getTimelapses(),
			getCameras(),
		])
		timelapses.value = tls
		cameras.value = cams
	} catch (err) {
		errorMessage.value = `Failed to load timelapses. (${err})`
		timelapses.value = []
		cameras.value = []
	} finally {
		isLoading.value = false
	}
}

onMounted(async () => {
	await fetchData()

	// handle errors passed by other pages/components
	if (route.query.error) {
		switch (route.query.error) {
			case 'timelapse_not_found':
				errorMessage.value = 'The timelapse you requested could not be found!'
				break
			default:
				errorMessage.value = String(route.query.error)
		}
	}
})

const statusMeta: Record<TimelapseStatus | 'scheduled', { dot: string; pill: string; label: string }> = {
	pending: { dot: 'bg-zinc-500', pill: 'bg-zinc-700/70 text-zinc-200', label: 'Pending' },
	scheduled: { dot: 'bg-indigo-400', pill: 'bg-indigo-900/70 text-indigo-200', label: 'Scheduled' },
	running: { dot: 'bg-emerald-500', pill: 'bg-emerald-900/70 text-emerald-200', label: 'Running' },
	paused: { dot: 'bg-amber-500', pill: 'bg-amber-900/70 text-amber-200', label: 'Paused' },
	completed: { dot: 'bg-sky-500', pill: 'bg-sky-900/70 text-sky-200', label: 'Completed' },
}

function statusKey(tl: TimelapseResponse): TimelapseStatus | 'scheduled' {
	if (tl.status === 'pending' && tl.started_at && new Date(tl.started_at) > new Date()) return 'scheduled'
	return tl.status
}
</script>

<template>
	<div>
		<div class="flex items-center justify-between mb-6">
			<div class="flex items-center gap-3">
				<h1 class="text-2xl font-semibold">Active Timelapses</h1>
				<PhSpinner v-if="isLoading" :size="24" class="text-zinc-700 dark:text-zinc-300 animate-spin" />
			</div>
			<TimelapseDialog :cameras="cameras" @timelapse-created="fetchData" />
		</div>

		<!-- Error alert -->
		<BaseAlert :open="errorMessage !== ''" :message="errorMessage" variant="error" :icon="PhWarningOctagon" dismissible @close="errorMessage = ''" />

		<div v-if="timelapses.length === 0" class="flex flex-col items-center justify-center py-24 text-muted-foreground gap-3">
			<PhVideoCamera :size="56" class="text-emerald-600/50" />
			<p class="text-lg font-semibold text-foreground">No timelapses yet</p>
			<p class="text-sm">Add a camera from the navbar to get started.</p>
		</div>

		<div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
			<a 
				v-for="timelapse in timelapses" :key="timelapse.id"
				:href="`/timelapse/${timelapse.id}`"
				class="flex flex-col border border-zinc-300/60 dark:border-zinc-800 rounded-xl overflow-hidden bg-zinc-100 dark:bg-zinc-900 hover:cursor-pointer hover:-translate-y-1 hover:shadow-lg hover:shadow-zinc-400/50 dark:hover:shadow-black/40 transition-all duration-200"
			>
				<!-- Thumbnail -->
				<div class="relative aspect-video w-full bg-radial from-white from-20% to-zinc-400 dark:from-zinc-800 dark:to-zinc-950">
					<!-- Fallback icon -->
					<span class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
						<!--PhCameraSlash weight="duotone" :size="64" class="mx-auto dark:drop-shadow-[0_0_35px_rgba(0,0,0,0.5)] drop-shadow-red-500 text-red-600/60 dark:text-red-500/60" /-->
						<PhCameraSlash weight="duotone" :size="56" class="mx-auto drop-shadow-[0_0_45px_rgba(0,0,0,1)] drop-shadow-white text-zinc-500 dark:text-zinc-400" />
						<span class="text-xs font-medium text-muted-foreground">No frames yet</span>
					</span>
					
					<!-- Last frame image -->
					<img v-if="timelapse.last_frame_id" :src="`/api/v1/frames/${timelapse.last_frame_id}/image`" class="absolute inset-0 w-full h-full object-cover" @error="(e) => ((e.currentTarget as HTMLImageElement).style.display = 'none')" />
					<!-- Bottom gradient for legibility -->
					<div v-if="timelapse.last_frame_id" class="absolute bottom-0 left-0 right-0 h-12 bg-linear-to-t from-zinc-800/60 dark:from-black/70 to-transparent pointer-events-none" />
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
