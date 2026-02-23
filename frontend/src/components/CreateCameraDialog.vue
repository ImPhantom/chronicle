<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Button } from '@/components/ui/button'
import {
	Dialog,
	DialogClose,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { CameraCreateRequest, CameraResponse, ConnectionType, HardwareCameraInfo, TestCaptureRequest } from '@/types'

const emit = defineEmits<{ 'camera-created': [camera: CameraResponse] }>()
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
const dialogOpen = ref(false)
const name = ref('')
const namePlaceholder = ref('Grow Tent #1')
const connectionType = ref<ConnectionType>('network')
const rtspUrl = ref('')
const deviceIndex = ref<number | null>(null)

const isNetwork = computed(() => connectionType.value === 'network')
const isHardware = computed(() => connectionType.value === 'hardware')

const hardwareCameras = ref<HardwareCameraInfo[]>([])
const selectedHardwareCameraIndex = ref<string>('')

const isTesting = ref(false)
const testCaptureUrl = ref<string | null>(null)
const testCaptureError = ref<string | null>(null)

const isSubmitting = ref(false)
const submitError = ref<string | null>(null)

async function fetchHardwareCameras() {
	try {
		const res = await fetch('/api/v1/cameras/hardware')
		hardwareCameras.value = await res.json()
		if (hardwareCameras.value.length > 0 && hardwareCameras.value[0]) {
			selectedHardwareCameraIndex.value = String(hardwareCameras.value[0].index)
			deviceIndex.value = hardwareCameras.value[0].index
		}
	} catch {
		hardwareCameras.value = []
	}
}

watch(connectionType, (val) => {
	if (val === 'hardware') fetchHardwareCameras()
})

watch(selectedHardwareCameraIndex, (val) => {
	deviceIndex.value = val !== '' ? Number(val) : null

	// Update placeholder to match cameras name (small visual improvment)
	const cam = hardwareCameras.value.find(c => String(c.index) === val)
	if (cam) namePlaceholder.value = cam.name
})

watch(dialogOpen, (open) => {
	if (!open) {
		if (testCaptureUrl.value) URL.revokeObjectURL(testCaptureUrl.value)
		testCaptureUrl.value = null
		testCaptureError.value = null
		submitError.value = null
		name.value = ''
		connectionType.value = 'network'
		rtspUrl.value = ''
		deviceIndex.value = null
		selectedHardwareCameraIndex.value = ''
	}
})

async function testCapture() {
	if (testCaptureUrl.value) { URL.revokeObjectURL(testCaptureUrl.value); testCaptureUrl.value = null }
	testCaptureError.value = null
	isTesting.value = true
	const payload: TestCaptureRequest = {
		connection_type: connectionType.value,
		...(isNetwork.value ? { rtsp_url: rtspUrl.value } : {}),
		...(isHardware.value && deviceIndex.value !== null ? { device_index: deviceIndex.value } : {}),
	}
	try {
		const res = await fetch('/api/v1/cameras/test-capture', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload),
		})
		if (!res.ok) {
			let detail = `Capture failed (HTTP ${res.status})`
			try { const j = await res.json(); if (j.detail) detail = j.detail } catch {}
			testCaptureError.value = detail
			return
		}
		testCaptureUrl.value = URL.createObjectURL(await res.blob())
	} catch (err) {
		testCaptureError.value = err instanceof Error ? err.message : 'Network error'
	} finally {
		isTesting.value = false
	}
}

async function handleSubmit() {
	submitError.value = null
	isSubmitting.value = true
	const payload: CameraCreateRequest = {
		name: name.value,
		connection_type: connectionType.value,
		...(isNetwork.value ? { rtsp_url: rtspUrl.value } : {}),
		...(isHardware.value && deviceIndex.value !== null ? { device_index: deviceIndex.value } : {}),
	}
	try {
		const res = await fetch('/api/v1/cameras', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload),
		})
		if (!res.ok) {
			let detail = `Failed to create camera (HTTP ${res.status})`
			try { const j = await res.json(); if (j.detail) detail = j.detail } catch {}
			submitError.value = detail
			return
		}
		const camera: CameraResponse = await res.json()
		emit('camera-created', camera)
		dialogOpen.value = false
	} catch (err) {
		submitError.value = err instanceof Error ? err.message : 'Network error'
	} finally {
		isSubmitting.value = false
	}
}
</script>

<template>
	<Dialog v-model:open="dialogOpen">
		<DialogTrigger as-child>
			<Button>
				Add Camera
			</Button>
		</DialogTrigger>
		<DialogContent class="sm:max-w-md">
			<form @submit.prevent="handleSubmit">
				<DialogHeader>
					<DialogTitle>Add Camera</DialogTitle>
					<DialogDescription>
						Configure a new camera source. Click save when you're done.
					</DialogDescription>
				</DialogHeader>
				<div class="grid gap-4 mt-4">
					<div class="grid gap-3">
						<Label for="name-1">Name</Label>
						<Input id="name-1" v-model="name" name="name" :placeholder="namePlaceholder" />
					</div>
					<div class="grid gap-3">
						<Label>Connection Type</Label>

						<Select v-model="connectionType">
							<SelectTrigger class="w-full">
								<SelectValue placeholder="Select connection type" />
							</SelectTrigger>

							<SelectContent>
								<SelectItem value="network">
									Network (RTSP)
								</SelectItem>
								<SelectItem value="hardware">
									Hardware Camera
								</SelectItem>
							</SelectContent>
						</Select>
					</div>
					<div v-if="isNetwork" class="grid gap-3">
						<Label for="rtsp-1">RTSP URL</Label>
						<Input id="rtsp-1" v-model="rtspUrl" name="rtsp_url" placeholder="rtsp://user:password@127.0.0.1:554/stream" />
					</div>
					<div v-if="isNetwork" class="grid gap-3">
						<Button type="button" variant="outline" size="sm" :disabled="isTesting || !rtspUrl" @click="testCapture">
							<span v-if="isTesting">Capturing...</span><span v-else>Test capture</span>
						</Button>
					</div>
					<div v-if="isHardware" class="grid gap-3">
						<Label>Hardware Camera</Label>

						<Select v-model="selectedHardwareCameraIndex">
							<SelectTrigger class="w-full">
								<SelectValue placeholder="Select a camera" />
							</SelectTrigger>

							<SelectContent>
								<SelectItem
									v-for="cam in hardwareCameras"
									:key="cam.index"
									:value="String(cam.index)"
									class="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-accent focus:text-accent-foreground"
								>
									{{ cam.name }} ({{ cam.index }})
								</SelectItem>
								<div v-if="hardwareCameras.length === 0" class="px-2 py-1.5 text-sm text-muted-foreground">
									No cameras detected
								</div>
							</SelectContent>
						</Select>
					</div>
					<div v-if="isHardware" class="grid gap-3">
						<Button type="button" variant="outline" size="sm" :disabled="isTesting || deviceIndex === null" @click="testCapture">
							<span v-if="isTesting">Capturing...</span><span v-else>Test capture</span>
						</Button>
					</div>
					<div v-if="testCaptureUrl || testCaptureError" class="grid gap-2">
						<img v-if="testCaptureUrl" :src="testCaptureUrl" alt="Test capture preview" class="w-full rounded-md border object-contain max-h-48" />
						<p v-if="testCaptureError" class="text-sm text-destructive">{{ testCaptureError }}</p>
					</div>
				</div>
				<DialogFooter class="flex-col items-start gap-2 sm:flex-row sm:items-center pt-3">
					<p v-if="submitError" class="text-sm text-destructive">{{ submitError }}</p>
					<div class="flex gap-2 sm:ml-auto">
						<DialogClose as-child>
							<Button variant="outline" :disabled="isSubmitting">
								Cancel
							</Button>
						</DialogClose>
						<Button type="submit" :disabled="isSubmitting">
							<span v-if="isSubmitting">Saving...</span><span v-else>Submit</span>
						</Button>
					</div>
				</DialogFooter>
			</form>
		</DialogContent>
	</Dialog>
</template>
