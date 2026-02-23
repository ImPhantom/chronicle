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
import {
	type AppSettingsResponse, type AppSettingsUpdateRequest,
	type CameraResponse, type CaptureImageFormat, type RtspTransport,
} from '@/types'
import { PhCamera, PhGear, PhTrash } from '@phosphor-icons/vue'
import { ref, reactive, onMounted } from 'vue'
import ConnectionTypeBadge from '@/components/ConnectionTypeBadge.vue'

const settings = ref<AppSettingsResponse | null>(null)
const cameras = ref<CameraResponse[]>([])
const cameraToDelete = ref<CameraResponse | null>(null)
const isDeletingCamera = ref(false)

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

const fetchCameras = async () => {
	try {
		const res = await fetch('/api/v1/cameras')
		cameras.value = await res.json()
	} catch {
		cameras.value = []
	}
}

const deleteCamera = async () => {
	if (isDeletingCamera.value) return
	if (!cameraToDelete.value) return
	isDeletingCamera.value = true
	try {
		const res = await fetch(`/api/v1/cameras/${cameraToDelete.value.id}`, { method: 'DELETE' })
		if (res.ok) {
			cameras.value = cameras.value.filter(cam => cam.id !== cameraToDelete.value?.id)
		}
	} finally {
		isDeletingCamera.value = false
		cameraToDelete.value = null
	}
}

const confirmDeleteCamera = (cam: CameraResponse) => {
	cameraToDelete.value = cam
}

onMounted(async () => {
	settings.value = await fetch('/api/v1/settings').then(res => res.json())
	await fetchCameras()

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
		const res = await fetch('/api/v1/settings', {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload),
		})
		if (!res.ok) {
			const data = await res.json().catch(() => null)
			saveError.value = data?.detail ?? `Error ${res.status}`
		} else {
			settings.value = await res.json()
		}
	} catch (e) {
		saveError.value = e instanceof Error ? e.message : 'Unknown error'
	} finally {
		isSaving.value = false
	}
}
</script>

<template>
	<div>
		<div class="flex items-center text-muted-foreground">
			<PhCamera size="32" weight="duotone" />
			<h1 class="text-2xl font-bold tracking-wide ml-2">Cameras</h1>
			<hr class="border-zinc-300 dark:border-zinc-700 w-full mx-4" />
			<CreateCameraDialog v-on:camera-created="fetchCameras" />
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
								Are you sure you want to delete this camera?
								This may affect currently running timelapses!
							</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel @click="cameraToDelete = null">Cancel</AlertDialogCancel>
							<AlertDialogAction @click="deleteCamera" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
								Delete
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</div>
		</div>

		<div class="flex items-center text-muted-foreground mt-6">
			<PhGear size="32" weight="duotone" />
			<h1 class="text-2xl font-bold tracking-wide ml-2">Settings</h1>
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
