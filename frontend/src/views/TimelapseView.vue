<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { TimelapseResponse, CameraResponse, FrameResponse, TimelapseStatus } from '@/types'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import ConnectionTypeBadge from '@/components/ConnectionTypeBadge.vue'
import { Button } from '@/components/ui/button'
import {
	AlertDialog, AlertDialogTrigger, AlertDialogContent,
	AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
	AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '@/components/ui/alert-dialog'
import {
	PhArrowLeft,
	PhPlay,
	PhPause,
	PhStop,
	PhImages,
	PhClock,
	PhCalendar,
	PhHardDrive,
	PhCameraSlash,
	PhCamera,
	PhSpinner,
	PhTrash,
} from '@phosphor-icons/vue'
import TimelapseStatusDot from '@/components/TimelapseStatusDot.vue'
import ExportDialog from '@/components/ExportDialog.vue'
import { formatBytes } from '@/lib/format'
import { deleteTimelapse, getTimelapse, updateTimelapse } from '@/api/timelapse'
import { getCamera } from '@/api/camera'
import { getFrame } from '@/api/frame'
import ExportSection from '@/components/timelapse/ExportSection.vue'

const exportSection = ref<InstanceType<typeof ExportSection> | null>(null)

const timelapse = ref<TimelapseResponse | null>(null)
const camera = ref<CameraResponse | null>(null)
const lastFrame = ref<FrameResponse | null>(null)
const isUpdating = ref(false)
const isDeleting = ref(false)
const imageError = ref(false)

const router = useRouter()
const route = useRoute()

const isScheduled = computed(() =>
	timelapse.value?.status === 'pending' &&
	!!timelapse.value.started_at &&
	new Date(timelapse.value.started_at) > new Date()
)

function formatDate(iso: string | null): string {
	if (!iso) return '—'
	return new Date(iso).toLocaleString(undefined, {
		dateStyle: 'long',
		timeStyle: 'short',
	})
}

async function updateStatus(newStatus: TimelapseStatus) {
	if (!timelapse.value) return
	isUpdating.value = true
	try {
		const body: Record<string, unknown> = { status: newStatus }
		if (newStatus === 'running' && timelapse.value.status !== 'paused') {
			body.started_at = new Date().toISOString()
		}
		if (newStatus === 'completed') {
			body.ended_at = new Date().toISOString()
		}

		const _tl = await updateTimelapse(timelapse.value.id, body)
		timelapse.value = _tl
	} catch (err) {
		console.error('Failed to update timelapse status:', err)
		timelapse.value = null
	} finally {
		isUpdating.value = false
	}
}

async function doTimelapseDelete() {
	if (!timelapse.value) return
	isDeleting.value = true
	try {
		await deleteTimelapse(timelapse.value.id)
		router.push('/')
	} finally {
		isDeleting.value = false
	}
}

const fetchData = async (tl: TimelapseResponse | null) => {
	if (!tl) return
	const [_camera, _lastFrame] = await Promise.all([
		getCamera(tl.camera_id),
		tl.last_frame_id ? getFrame(tl.last_frame_id) : Promise.resolve(null),
	])

	camera.value = _camera
	lastFrame.value = _lastFrame
}

onMounted(async () => {
	if (!route.params.id) {
		router.push('/')
		return
	}
	const id = parseInt(route.params.id as string)
	try {
		timelapse.value = await getTimelapse(id)
		await fetchData(timelapse.value)
	} catch {
		timelapse.value = null
		router.push('/')
		return
	}
})
</script>

<template>
	<div v-if="timelapse" class="space-y-6">
		<!-- Back link -->
		<RouterLink to="/" class="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
			<PhArrowLeft variant="duotone" :size="16" />
			Back to Dashboard
		</RouterLink>

		<!-- Header -->
		<div class="flex items-start justify-between gap-4">
			<div class="space-y-1">
				<h1 class="text-2xl font-semibold">{{ timelapse.name }}</h1>
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<TimelapseStatusDot :status="timelapse.status" :scheduled="isScheduled" />
					<span>·</span>
					<span>every {{ timelapse.interval_seconds }}s</span>
				</div>
			</div>

			<!-- Controls -->
			<div class="flex items-center gap-2 shrink-0">
				<template v-if="timelapse.status === 'pending'">
					<Button size="sm" :disabled="isUpdating" @click="updateStatus('running')" class="bg-emerald-600 hover:bg-emerald-700 text-white">
						<PhSpinner v-if="isUpdating" variant="duotone" class="animate-spin" />
						<PhPlay v-else variant="duotone" />
						Start
					</Button>
				</template>
				<template v-else-if="timelapse.status === 'running'">
					<Button size="sm" variant="outline" :disabled="isUpdating" @click="updateStatus('paused')" class="border-amber-500 text-amber-400 hover:bg-amber-500/10">
						<PhSpinner v-if="isUpdating" variant="duotone" class="animate-spin" />
						<PhPause v-else variant="duotone" />
						Pause
					</Button>
					<Button size="sm" variant="outline" :disabled="isUpdating" @click="updateStatus('completed')" class="border-red-500 text-red-400 hover:bg-red-500/10">
						<PhSpinner v-if="isUpdating" variant="duotone" class="animate-spin" />
						<PhStop v-else variant="duotone" />
						Stop
					</Button>
				</template>
				<template v-else-if="timelapse.status === 'paused'">
					<Button size="sm" :disabled="isUpdating" @click="updateStatus('running')" class="bg-emerald-600 hover:bg-emerald-700 text-white">
						<PhSpinner v-if="isUpdating" variant="duotone" class="animate-spin" />
						<PhPlay v-else variant="duotone" />
						Resume
					</Button>
					<Button size="sm" variant="outline" :disabled="isUpdating" @click="updateStatus('completed')" class="border-red-500 text-red-400 hover:bg-red-500/10">
						<PhSpinner v-if="isUpdating" variant="duotone" class="animate-spin" />
						<PhStop v-else variant="duotone" />
						Stop
					</Button>
				</template>
				<template v-else-if="timelapse.status === 'completed'">
					<span class="text-sm text-muted-foreground">Completed</span>
				</template>

				<!-- Export (shown when frames exist) -->
				<ExportDialog
					v-if="timelapse.frame_count > 0"
					:timelapse-id="timelapse.id"
					:frame-count="timelapse.frame_count"
					@job-started="(job) => exportSection?.onJobStarted(job)"
				/>

				<!-- Delete (always shown) -->
				<AlertDialog>
					<AlertDialogTrigger as-child>
						<Button size="sm" variant="outline" class="border-red-500 text-red-400 hover:bg-red-500/10" :disabled="isDeleting">
							<PhTrash variant="duotone" />
							Delete
						</Button>
					</AlertDialogTrigger>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>Delete timelapse?</AlertDialogTitle>
							<AlertDialogDescription>
								This will permanently delete "{{ timelapse.name }}" and all its captured frames.
								This action cannot be undone.
							</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel>Cancel</AlertDialogCancel>
							<AlertDialogAction @click="doTimelapseDelete" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
								Delete
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</div>
		</div>

		<!-- Scheduled info banner -->
		<div v-if="isScheduled" class="flex items-center gap-3 px-4 py-3 rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-sm text-indigo-300">
			<PhClock variant="duotone" :size="18" class="shrink-0 text-indigo-400" />
			<span>
				This timelapse is <strong>scheduled to start</strong> on
				<strong>{{ formatDate(timelapse.started_at) }}</strong>.
				It will begin capturing automatically.
			</span>
		</div>

		<!-- Main content grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
			<!-- Last frame (left, 2 cols) -->
			<div class="lg:col-span-2 self-start border rounded-lg bg-zinc-100 dark:bg-zinc-900 p-4 space-y-3">
				<h2 class="text-sm font-medium flex items-center gap-2">
					<PhImages variant="duotone" :size="18" class="text-zinc-400" />
					Last Frame
				</h2>

				<div class="relative aspect-video w-full rounded-md bg-zinc-300/70 dark:bg-zinc-800/60 border overflow-hidden">
					<img
						v-if="lastFrame && !imageError"
						:src="`/api/v1/frames/${lastFrame.id}/image`"
						class="w-full h-full object-contain"
						@error="imageError = true"
					/>
					<div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-2 text-muted-foreground">
						<PhCameraSlash variant="duotone" :size="80" class="text-red-400/40" />
						<span class="text-sm">No frames captured yet</span>
					</div>
				</div>

				<p v-if="lastFrame" class="text-xs text-muted-foreground flex items-center gap-1.5">
					<PhClock variant="duotone" :size="14" />
					Captured {{ formatDate(lastFrame.captured_at) }}
				</p>
			</div>

			<!-- Right column -->
			<div class="space-y-4">
				<!-- Camera info -->
				<div class="border rounded-lg bg-zinc-100 dark:bg-zinc-900 p-4 space-y-3">
					<h2 class="text-sm font-medium flex items-center gap-2">
						<PhCamera variant="duotone" :size="18" class="text-zinc-400" />
						Camera
					</h2>
					<div v-if="camera" class="space-y-2">
						<div class="flex items-center gap-2">
							<span class="text-sm font-medium">{{ camera.name }}</span>
							<ConnectionTypeBadge :cam="camera" />
						</div>
						<p v-if="camera.rtsp_url" class="text-xs text-muted-foreground truncate" :title="camera.rtsp_url">
							{{ camera.rtsp_url.replace(/rtsp:\/\/[^@]+@/, "rtsp://") }}
						</p>
						<p v-else class="text-xs text-muted-foreground">No RTSP URL configured</p>
					</div>
					<p v-else class="text-sm text-muted-foreground">Unknown camera</p>
				</div>

				<!-- Statistics -->
				<div class="border rounded-lg bg-zinc-100 dark:bg-zinc-900 p-4 space-y-3">
					<h2 class="text-sm font-medium flex items-center gap-2">
						<PhCalendar variant="duotone" :size="18" class="text-zinc-400" />
						Statistics
					</h2>
					<dl class="space-y-2 text-sm">
						<div class="flex justify-between">
							<dt class="text-muted-foreground flex items-center gap-1.5">
								<PhImages variant="duotone" :size="14" />
								Frames
							</dt>
							<dd class="font-medium">{{ timelapse.frame_count }}</dd>
						</div>
						<div class="flex justify-between">
							<dt class="text-muted-foreground flex items-center gap-1.5">
								<PhClock variant="duotone" :size="14" />
								Interval
							</dt>
							<dd class="font-medium">{{ timelapse.interval_seconds }} seconds</dd>
						</div>
						<div class="flex justify-between">
							<dt class="text-muted-foreground flex items-center gap-1.5">
								<PhCalendar variant="duotone" :size="14" />
								Created
							</dt>
							<dd class="font-medium">{{ formatDate(timelapse.created_at) }}</dd>
						</div>
						<div class="flex justify-between">
							<dt class="text-muted-foreground flex items-center gap-1.5">
								<PhPlay variant="duotone" :size="14" />
								{{ isScheduled ? 'Scheduled for' : 'Started' }}
							</dt>
							<dd class="font-medium" :class="{ 'text-indigo-300': isScheduled }">
								{{ formatDate(timelapse.started_at) }}
							</dd>
						</div>
						<div v-if="timelapse.ended_at" class="flex justify-between">
							<dt class="text-muted-foreground flex items-center gap-1.5">
								<PhStop variant="duotone" :size="14" />
								Ended
							</dt>
							<dd class="font-medium">{{ formatDate(timelapse.ended_at) }}</dd>
						</div>
						<div class="flex justify-between">
							<dt class="text-muted-foreground flex items-center gap-1.5">
								<PhHardDrive variant="duotone" :size="14" />
								Disk usage
							</dt>
							<dd class="font-medium">{{ formatBytes(timelapse.size_bytes) }}</dd>
						</div>
					</dl>
				</div>

				<ExportSection ref="exportSection" :timelapse-id="timelapse.id" />
			</div>
		</div>
	</div>
</template>
