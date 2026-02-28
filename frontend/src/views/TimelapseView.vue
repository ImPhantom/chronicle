<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { TimelapseResponse, CameraResponse, FrameResponse, TimelapseStatus, AppSettingsResponse } from '@/types'
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
	PhWarningOctagon,
} from '@phosphor-icons/vue'
import TimelapseStatusDot from '@/components/TimelapseStatusDot.vue'
import ExportDialog from '@/components/ExportDialog.vue'
import { formatBytes } from '@/lib/format'
import { deleteTimelapse, getTimelapse, updateTimelapse } from '@/api/timelapse'
import { getCamera } from '@/api/camera'
import { getFrame } from '@/api/frame'
import ExportSection from '@/components/timelapse/ExportSection.vue'
import FrameExplorerSection from '@/components/timelapse/FrameExplorerSection.vue'
import { getSettings } from '@/api/settings'
import BaseAlert from '@/components/BaseAlert.vue'
import { ButtonGroup } from '@/components/ui/button-group'
import Separator from '@/components/ui/separator/Separator.vue'

const exportSection = ref<InstanceType<typeof ExportSection> | null>(null)

const timelapse = ref<TimelapseResponse | null>(null)
const camera = ref<CameraResponse | null>(null)
const lastFrame = ref<FrameResponse | null>(null)
const settings = ref<AppSettingsResponse | null>(null)
const isUpdating = ref(false)
const isDeleting = ref(false)
const imageError = ref(false)
const errorMessage = ref('')

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
		errorMessage.value = `Failed to update timelapse status!\r\n${err}`
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
	} catch (err) {
		errorMessage.value = `Failed to delete timelapse! (${err instanceof Error ? err.message : 'Unknown error'})`
	} finally {
		isDeleting.value = false
	}
}

const fetchData = async (tl: TimelapseResponse | null) => {
	if (!tl) return
	const [_camera, _lastFrame, _settings] = await Promise.all([
		getCamera(tl.camera_id),
		tl.last_frame_id ? getFrame(tl.last_frame_id) : Promise.resolve(null),
		getSettings(),
	])

	camera.value = _camera
	lastFrame.value = _lastFrame
	settings.value = _settings
}

async function refreshTimelapse() {
	if (!timelapse.value) return
	timelapse.value = await getTimelapse(timelapse.value.id)
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
		router.push('/?error=timelapse_not_found')
		return
	}
})
</script>

<template>
	<div v-if="timelapse" class="space-y-5">
		<!-- Back link -->
		<RouterLink to="/" class="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
			<PhArrowLeft variant="duotone" :size="16" />
			Back to Dashboard
		</RouterLink>

		<!-- Header -->
		<div class="flex items-end justify-between gap-4">
			<div class="space-y-1">
				<h1 class="text-2xl font-semibold">{{ timelapse.name }}</h1>
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<TimelapseStatusDot :status="timelapse.status" :scheduled="isScheduled" />
					<span>·</span>
					<span>every {{ timelapse.interval_seconds }}s</span>
				</div>
			</div>

			<!-- Controls -->
			<div class="flex items-center gap-3 shrink-0">
				<template v-if="timelapse.status === 'pending'">
					<Button variant="outline" :disabled="isUpdating" @click="updateStatus('running')">
						<PhSpinner v-if="isUpdating" class="animate-spin" />
						<PhPlay v-else weight="duotone" class="text-emerald-600" />
						{{ isScheduled ? 'Start Now' : 'Start' }}
					</Button>
				</template>
				<template v-else-if="timelapse.status === 'running'">
					<ButtonGroup>
						<Button variant="outline" :disabled="isUpdating" @click="updateStatus('paused')">
							<PhSpinner v-if="isUpdating" class="animate-spin" />
							<PhPause v-else weight="duotone" class="text-amber-400" />
							Pause
						</Button>
						<Button variant="outline" :disabled="isUpdating" @click="updateStatus('completed')">
							<PhSpinner v-if="isUpdating" class="animate-spin" />
							<PhStop v-else weight="duotone" class="text-red-400" />
							Stop
						</Button>
					</ButtonGroup>
				</template>
				<template v-else-if="timelapse.status === 'paused'">
					<ButtonGroup>
						<Button variant="outline" :disabled="isUpdating" @click="updateStatus('running')">
							<PhSpinner v-if="isUpdating" class="animate-spin" />
							<PhPlay v-else weight="duotone" class="text-emerald-600" />
							Resume
						</Button>
						<Button variant="outline" :disabled="isUpdating" @click="updateStatus('completed')">
							<PhSpinner v-if="isUpdating" class="animate-spin" />
							<PhStop v-else weight="duotone" class="text-red-400" />
							Stop
						</Button>
					</ButtonGroup>
				</template>

				<!-- Export (shown when frames exist) -->
				<ExportDialog
					v-if="timelapse.frame_count > 0"
					:timelapse-id="timelapse.id"
					:frame-count="timelapse.frame_count"
					@job-started="(job) => exportSection?.onJobStarted(job)"
				/>

				<span class="h-6">
					<Separator orientation="vertical" />
				</span>

				<!-- Delete (always shown) -->
				<AlertDialog>
					<AlertDialogTrigger as-child>
						<Button variant="destructive" :disabled="isDeleting">
							<PhTrash weight="duotone" />
							Delete
						</Button>
					</AlertDialogTrigger>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>Delete timelapse: {{ timelapse.name }}?</AlertDialogTitle>
							<AlertDialogDescription>
								This will permanently remove all associated files from disk<br>
								<strong>This action cannot be undone.</strong>

								<pre class="mt-2 px-2 py-1 text-xs bg-zinc-200/60 dark:bg-zinc-800/60 rounded-sm text-blue-600 dark:text-blue-400">{{settings?.storage_path}}/timelapse_{{ timelapse.id }}
{{settings?.storage_path}}/exports/timelapse_{{ timelapse.id }}_*.(mp4|webm)</pre>
									<span class="text-xs text-muted-foreground">(if you wish to back the files up)</span>
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
		<BaseAlert :open="isScheduled" variant="info" :icon="PhClock">
			<span>
				This timelapse is <strong>scheduled to start</strong> on
				<strong>{{ formatDate(timelapse.started_at) }}</strong>.
				It will begin capturing automatically.
			</span>
		</BaseAlert>

		<!-- Error banner -->
		<BaseAlert :open="errorMessage !== ''" :message="errorMessage" variant="error" :icon="PhWarningOctagon" dismissible @close="errorMessage = ''" />

		<!-- Main content grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
			<!-- Last frame (left, 2 cols) -->
			<div class="lg:col-span-2 self-start border rounded-lg bg-zinc-100 dark:bg-zinc-900 p-4 space-y-3">
				<h2 class="text-sm font-medium flex items-center gap-2">
					<PhImages variant="duotone" :size="18" class="text-zinc-400" />
					Last Frame
				</h2>

				<div class="relative aspect-video w-full rounded-md bg-radial from-white from-20% to-zinc-300 dark:from-zinc-800 dark:to-zinc-950 border overflow-hidden">
					<img
						v-if="lastFrame && !imageError"
						:src="`/api/v1/frames/${lastFrame.id}/image`"
						class="w-full h-full object-contain"
						@error="imageError = true"
					/>
					<div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-2 text-muted-foreground">
						<PhCameraSlash weight="duotone" :size="56" class="mx-auto drop-shadow-[0_0_45px_rgba(0,0,0,1)] drop-shadow-white text-zinc-500 dark:text-zinc-400" />
						<span class="text-xs">No frames captured yet</span>
					</div>
				</div>

				<p v-if="lastFrame" class="text-xs text-muted-foreground flex items-center gap-1.5">
					<PhClock variant="duotone" :size="14" />
					Captured {{ formatDate(lastFrame.captured_at) }}
				</p>
			</div>

			<!-- Right column -->
			<div class="flex flex-col gap-4">
				<!-- Camera info -->
				<div class="shrink-0 border rounded-lg bg-zinc-100 dark:bg-zinc-900 p-4 space-y-3">
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
				<div class="shrink-0 border rounded-lg bg-zinc-100 dark:bg-zinc-900 p-4 space-y-3">
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

				<div class="relative flex-1 min-h-48">
					<div class="absolute inset-0">
						<ExportSection
							ref="exportSection"
							:timelapse-id="timelapse.id"
							:storage-path="settings?.storage_path"
							@error="(msg) => errorMessage = msg"
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- Frame explorer -->
		<FrameExplorerSection
			v-if="timelapse.frame_count > 0"
			:timelapse-id="timelapse.id"
			:frame-count="timelapse.frame_count"
			@error="(msg) => errorMessage = msg"
			@frame-deleted="refreshTimelapse"
		/>
	</div>
</template>
