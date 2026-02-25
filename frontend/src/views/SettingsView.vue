<script setup lang="ts">
import CreateCameraDialog from '@/components/CreateCameraDialog.vue'
import {
	Field,
	FieldDescription,
	FieldGroup,
	FieldLabel,
	FieldSet,
} from '@/components/ui/field'
import Input from '@/components/ui/input/Input.vue';
import {
	Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
	AlertDialog, AlertDialogContent,
	AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
	AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import type {
	AppSettingsResponse, AppSettingsUpdateRequest,
	CameraResponse, CaptureImageFormat, RtspTransport,
	StorageStats, TimelapseResponse,
} from '@/types'
import { PhCamera, PhGear, PhHardDrive, PhSpinner, PhTrash, PhWarningOctagon } from '@phosphor-icons/vue'
import { ref, reactive, onMounted, computed } from 'vue'
import { formatBytes } from '@/lib/format'

import ConnectionTypeBadge from '@/components/ConnectionTypeBadge.vue'
import { getSettings, getStorageStats, updateSettings } from '@/api/settings';
import { getTimelapses } from '@/api/timelapse';
import { deleteCamera, getCameras } from '@/api/camera';
import BaseAlert from '@/components/BaseAlert.vue';

const settings = ref<AppSettingsResponse | null>(null)
const cameras = ref<CameraResponse[]>([])
const cameraToDelete = ref<CameraResponse | null>(null)
const isDeletingCamera = ref(false)
const storageStats = ref<StorageStats | null>(null)
const timelapses = ref<TimelapseResponse[]>([])
const errorMessage = ref<string>('')
const isLoading = ref(true)

const usedPercent = computed(() => {
	if (!storageStats.value || storageStats.value.total_bytes === 0) return 0
	return (storageStats.value.used_bytes / storageStats.value.total_bytes) * 100
})

const form = reactive({
	timezone: '',
	storage_path: '',
	max_storage_gb: '',
	retention_days: '',
	default_capture_interval_seconds: '',
	capture_image_format: 'webp' as CaptureImageFormat,
	capture_image_quality: '',
	max_frames_per_timelapse: '',
	ffmpeg_timeout_seconds: '',
	ffmpeg_rtsp_transport: 'tcp' as RtspTransport,
})

const isSaving = ref(false)
const saveError = ref<string | null>(null)

// This is split off so it can be triggered by CreateCameraDialog's event
const refreshCameras = async () => 
	await getCameras().then(_cams => cameras.value = _cams).catch(err => {
		console.error('failed to fetch cameras!', err)
		cameras.value = []
	})

const doCameraDelete = async () => {
	if (isDeletingCamera.value) return
	if (!cameraToDelete.value) return
	isDeletingCamera.value = true
	try {
		await deleteCamera(cameraToDelete.value.id)
		// Remove from local array instead of another fetch
		cameras.value = cameras.value.filter(cam => cam.id !== cameraToDelete.value?.id)
	} finally {
		isDeletingCamera.value = false
		cameraToDelete.value = null
	}
}

const confirmDeleteCamera = (cam: CameraResponse) => {
	cameraToDelete.value = cam
}

const getAssociatedCameraFiles = (cameraId?: number) => {
	const tls = timelapses.value.filter(tl => tl.camera_id === cameraId)
	let toBeRemoved = ""
	for (const tl of tls) {
		toBeRemoved += `${settings.value?.storage_path}/timelapse_${tl.id}/\r\n`
		toBeRemoved += `${settings.value?.storage_path}/exports/timelapse_${tl.id}_*.*\r\n`
	}

	return toBeRemoved
}

onMounted(async () => {
	isLoading.value = true
	try {
		const [_settings, _storageStats, _timelapses] = await Promise.all([
			getSettings(),
			getStorageStats(),
			getTimelapses(),
			refreshCameras(),
		]);
		
		settings.value = _settings
		storageStats.value = _storageStats
		timelapses.value = _timelapses
		// No need to set 'cameras', 'refreshCameras' already does so.
	} catch (err) {
		errorMessage.value = `Failed to load data from API (${err})`
		settings.value = null
		storageStats.value = null
		timelapses.value = []
	} finally {
		isLoading.value = false
	}

	if (settings.value) {
		const s = settings.value
		form.timezone = s.timezone
		form.storage_path = s.storage_path
		form.max_storage_gb = s.max_storage_gb != null ? String(s.max_storage_gb) : ''
		form.retention_days = s.retention_days != null ? String(s.retention_days) : ''
		form.default_capture_interval_seconds = String(s.default_capture_interval_seconds)
		form.capture_image_format = s.capture_image_format
		form.capture_image_quality = String(s.capture_image_quality)
		form.max_frames_per_timelapse = s.max_frames_per_timelapse != null ? String(s.max_frames_per_timelapse) : ''
		form.ffmpeg_timeout_seconds = String(s.ffmpeg_timeout_seconds)
		form.ffmpeg_rtsp_transport = s.ffmpeg_rtsp_transport
	}
})

async function saveSettings() {
	isSaving.value = true
	saveError.value = null

	const payload: AppSettingsUpdateRequest = {
		timezone: form.timezone,
		storage_path: form.storage_path,
		max_storage_gb: form.max_storage_gb !== '' ? Number(form.max_storage_gb) : null,
		retention_days: form.retention_days !== '' ? Number(form.retention_days) : null,
		default_capture_interval_seconds: Number(form.default_capture_interval_seconds),
		capture_image_format: form.capture_image_format,
		capture_image_quality: Number(form.capture_image_quality),
		max_frames_per_timelapse: form.max_frames_per_timelapse !== '' ? Number(form.max_frames_per_timelapse) : null,
		ffmpeg_timeout_seconds: Number(form.ffmpeg_timeout_seconds),
		ffmpeg_rtsp_transport: form.ffmpeg_rtsp_transport,
	}

	try {
		const _settings = await updateSettings(payload)
		settings.value = _settings
	} catch (e) {
		saveError.value = e instanceof Error ? e.message : 'Unknown error'
	} finally {
		isSaving.value = false
	}
}
</script>

<template>
	<div>
		<!-- Error alert -->
		<BaseAlert :open="errorMessage !== ''" :message="errorMessage" variant="error" :icon="PhWarningOctagon" dismissible @close="errorMessage = ''" class="mb-6" />

		<div class="flex items-center text-muted-foreground">
			<PhCamera size="32" weight="duotone" />
			<h1 class="text-2xl font-bold tracking-wide ml-2">Cameras</h1>
			<PhSpinner v-if="isLoading" :size="24" class="ml-3 text-zinc-700 dark:text-zinc-300 animate-spin" />
			<hr class="border-zinc-300 dark:border-zinc-700 w-full mx-4" />
			<CreateCameraDialog v-on:camera-created="refreshCameras" />
		</div>

		<div class="p-3">
			<div v-if="cameras.length === 0" class="flex flex-col items-center justify-center py-24 text-muted-foreground gap-2">
				<p class="text-sm">No cameras setup yet!</p>
			</div>

			<div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
				<div v-for="cam in cameras" :key="cam.id" class="border rounded-lg px-4 py-3 bg-zinc-100 dark:bg-zinc-900">
					<div class="flex items-center">
						<h3 class="text-lg font-semibold">{{ cam.name }}</h3>
						<ConnectionTypeBadge :cam="cam" />

						<button 
							class="p-0.5 ml-auto text-zinc-500 hover:text-red-500/50 transition-colors"
							type="button"
							:disabled="isDeletingCamera"
							@click="confirmDeleteCamera(cam)"
						>
							<PhTrash size="22" weight="duotone" />
						</button>
					</div>
					<p class="text-sm text-muted-foreground mb-1">ID: {{ cam.id }}</p>
					<p v-if="cam.connection_type === 'network'" class="text-sm text-muted-foreground mb-1">URL: {{ cam.rtsp_url?.replace(/rtsp:\/\/[^@]+@/, "rtsp://") }}</p>
					<p v-if="cam.connection_type === 'hardware'" class="text-sm text-muted-foreground mb-1">Device Index: {{ cam.device_index }}</p>
				</div>

				<AlertDialog :open="cameraToDelete !== null">
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>Delete camera '{{ cameraToDelete?.name }}'?</AlertDialogTitle>
							<AlertDialogDescription>
								Are you absolutely sure you want to delete this camera?<br>
								This will delete all timelapses, frames and exports associated with this camera!<br>
								<strong>This action cannot be undone.</strong>
								<pre class="mt-2 px-2 py-1 text-xs bg-zinc-200/60 dark:bg-zinc-800/60 rounded-sm text-blue-600 dark:text-blue-400">{{ getAssociatedCameraFiles(cameraToDelete?.id) }}</pre>
								<span class="text-xs text-muted-foreground">(if you wish to back the files up)</span>
							</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel @click="cameraToDelete = null">Cancel</AlertDialogCancel>
							<AlertDialogAction @click="doCameraDelete" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
								Delete
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</div>
		</div>

		<!-- TODO: Improve the look of this section? -->
		<!-- Maybe only show the top 3-5 largest timelapses, and make the section collapsible -->
		<div class="flex items-center text-muted-foreground mt-6">
			<PhHardDrive size="32" weight="duotone" />
			<h1 class="text-2xl font-bold tracking-wide ml-2">Storage</h1>
			<PhSpinner v-if="isLoading" :size="24" class="ml-3 text-zinc-700 dark:text-zinc-300 animate-spin" />
			<hr class="border-zinc-300 dark:border-zinc-700 w-full ml-4" />
		</div>

		<div class="p-3">
			<div v-if="storageStats" class="mb-4">
				<div class="flex justify-between text-sm text-muted-foreground mb-1">
					<span>{{ formatBytes(storageStats.used_bytes) }} used</span>
					<span>{{ formatBytes(storageStats.free_bytes) }} free of {{ formatBytes(storageStats.total_bytes) }}</span>
				</div>
				<div class="w-full h-2 rounded-full bg-zinc-200 dark:bg-zinc-700 overflow-hidden">
					<div
						class="h-full rounded-full bg-primary transition-all"
						:style="{ width: `${usedPercent.toFixed(1)}%` }"
					/>
				</div>
			</div>

			<div v-if="timelapses.length > 0" class="mt-3">
				<table class="w-full text-sm">
					<thead>
						<tr class="text-left text-muted-foreground border-b border-zinc-200 dark:border-zinc-700">
							<th class="pb-1 font-medium">Timelapse</th>
							<th class="pb-1 font-medium text-right">Frames</th>
							<th class="pb-1 font-medium text-right">Size</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="tl in timelapses"
							:key="tl.id"
							class="border-b border-zinc-100 dark:border-zinc-800 last:border-0"
						>
							<td class="py-1.5">{{ tl.name }}</td>
							<td class="py-1.5 text-right text-muted-foreground">{{ tl.frame_count.toLocaleString() }}</td>
							<td class="py-1.5 text-right text-muted-foreground">{{ formatBytes(tl.size_bytes) }}</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-else class="text-sm text-muted-foreground py-4 text-center">No timelapses yet.</div>
		</div>

		<div class="flex items-center text-muted-foreground mt-6">
			<PhGear size="32" weight="duotone" />
			<h1 class="text-2xl font-bold tracking-wide ml-2">Settings</h1>
			<PhSpinner v-if="isLoading" :size="24" class="ml-3 text-zinc-700 dark:text-zinc-300 animate-spin" />
			<hr class="border-zinc-300 dark:border-zinc-700 w-full ml-4" />
		</div>

		<form class="mt-4 mb-6" @submit.prevent="saveSettings">
			<div class="flex flex-col sm:flex-row gap-8 px-4">
				<div class="basis-full sm:basis-1/2">
					<h2 class="text-xl font-semibold">General</h2>
					<p class="text-sm text-muted-foreground mb-4">Configure general application settings.</p>

					<FieldSet>
						<FieldGroup>
							<Field>
								<FieldLabel for="timezone">Timezone</FieldLabel>
								<Input id="timezone" type="text" placeholder="America/New_York" v-model="form.timezone" />
								<FieldDescription>
									IANA timezone string for timestamping captures. (e.g. "America/New_York", "UTC", "Asia/Seoul")
								</FieldDescription>
							</Field>

							<Field>
								<FieldLabel for="storage_path">Storage Path</FieldLabel>
								<Input id="storage_path" type="text" v-model="form.storage_path" />
								<FieldDescription>
									Directory where captured frames are stored.
								</FieldDescription>
							</Field>

							<Field>
								<FieldLabel for="max_storage_gb">Max Storage (GB)</FieldLabel>
								<Input id="max_storage_gb" type="number" placeholder="Unlimited" v-model="form.max_storage_gb" />
								<FieldDescription>
									Maximum total disk usage for stored frames. Leave blank for no limit.
								</FieldDescription>
							</Field>

							<Field>
								<FieldLabel for="retention_days">Retention (days)</FieldLabel>
								<Input id="retention_days" type="number" placeholder="Forever" v-model="form.retention_days" />
								<FieldDescription>
									Delete frames older than this many days. Leave blank to keep forever.
								</FieldDescription>
							</Field>
						</FieldGroup>
					</FieldSet>
				</div>

				<div class="basis-full sm:basis-1/2">
					<h2 class="text-xl font-semibold">Capture</h2>
					<p class="text-sm text-muted-foreground mb-4">Configure capture/FFMPEG settings.</p>

					<FieldSet>
						<FieldGroup>
							<Field>
								<FieldLabel for="default_capture_interval_seconds">Capture Interval (s)</FieldLabel>
								<Input id="default_capture_interval_seconds" type="number" min="1" v-model="form.default_capture_interval_seconds" />
								<FieldDescription>
									Default interval in seconds between frame captures.
								</FieldDescription>
							</Field>

							<Field>
								<FieldLabel>Image Format</FieldLabel>
								<Select v-model="form.capture_image_format">
									<SelectTrigger class="w-full">
										<SelectValue />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="webp">webp</SelectItem>
										<SelectItem value="jpeg">jpeg</SelectItem>
										<SelectItem value="png">png</SelectItem>
									</SelectContent>
								</Select>
								<FieldDescription>
									Image format used when saving captured frames.
								</FieldDescription>
							</Field>

							<Field>
								<FieldLabel for="capture_image_quality">Image Quality (1–100)</FieldLabel>
								<Input id="capture_image_quality" type="number" min="1" max="100" v-model="form.capture_image_quality" />
								<FieldDescription>
									Compression quality for captured frames.
								</FieldDescription>
							</Field>

							<Field>
								<FieldLabel for="max_frames_per_timelapse">Max Frames</FieldLabel>
								<Input id="max_frames_per_timelapse" type="number" placeholder="Unlimited" v-model="form.max_frames_per_timelapse" />
								<FieldDescription>
									Maximum frames stored per timelapse. Leave blank for no limit.
								</FieldDescription>
							</Field>

							<Field>
								<FieldLabel for="ffmpeg_timeout_seconds">FFmpeg Timeout (s)</FieldLabel>
								<Input id="ffmpeg_timeout_seconds" type="number" min="1" v-model="form.ffmpeg_timeout_seconds" />
								<FieldDescription>
									Seconds before an FFmpeg capture attempt times out.
								</FieldDescription>
							</Field>

							<Field>
								<FieldLabel>RTSP Transport</FieldLabel>
								<Select v-model="form.ffmpeg_rtsp_transport">
									<SelectTrigger class="w-full">
										<SelectValue />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="tcp">tcp</SelectItem>
										<SelectItem value="udp">udp</SelectItem>
										<SelectItem value="http">http</SelectItem>
									</SelectContent>
								</Select>
								<FieldDescription>
									Transport protocol used by FFmpeg for RTSP streams.
								</FieldDescription>
							</Field>
						</FieldGroup>
					</FieldSet>
				</div>
			</div>

			<div class="flex items-center justify-end gap-3 mt-6">
				<p v-if="saveError" class="text-sm text-destructive">{{ saveError }}</p>
				<Button type="submit" :disabled="isSaving">
					{{ isSaving ? 'Saving…' : 'Save Settings' }}
				</Button>
			</div>
		</form>
	</div>
</template>
