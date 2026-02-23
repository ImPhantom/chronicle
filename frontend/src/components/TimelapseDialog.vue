<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
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
import {
	Field,
	FieldDescription,
	FieldGroup,
	FieldLabel,
	FieldSet,
} from '@/components/ui/field'
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import type { CameraResponse, TimelapseResponse, TimelapseCreateRequest } from '@/types'
import { PhWarning } from '@phosphor-icons/vue'

const emit = defineEmits<{ 'timelapse-created': [timelapse: TimelapseResponse] }>()

const dialogOpen = ref(false)
const cameras = ref<CameraResponse[]>([])

// Core form fields
const form = ref({
	camera_id: 0,
	name: '',
	interval_seconds: 60,
})

// Schedule state (kept separate to avoid type issues with empty strings)
const startImmediately = ref(true)
const isIndefinite = ref(true)
const scheduledStart = ref('')
const scheduledEnd = ref('')

const isSubmitting = ref(false)
const submitError = ref<string | null>(null)

function resetForm() {
	form.value = { camera_id: 0, name: '', interval_seconds: 60 }
	startImmediately.value = true
	isIndefinite.value = true
	scheduledStart.value = ''
	scheduledEnd.value = ''
	submitError.value = null
}

watch(dialogOpen, (open) => {
	if (!open) resetForm()
})

async function handleSubmit() {
	submitError.value = null
	isSubmitting.value = true

	try {
		const payload: TimelapseCreateRequest = {
			camera_id: form.value.camera_id,
			name: form.value.name,
			interval_seconds: form.value.interval_seconds,
			status: startImmediately.value ? 'running' : 'pending',
			started_at: startImmediately.value
				? new Date().toISOString()
				: (scheduledStart.value ? new Date(scheduledStart.value).toISOString() : null),
			ended_at: isIndefinite.value
				? null
				: (scheduledEnd.value ? new Date(scheduledEnd.value).toISOString() : null),
		}

		const res = await fetch('/api/v1/timelapses', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload),
		})

		if (!res.ok) {
			const data = await res.json().catch(() => null)
			throw new Error(data?.detail ?? `Request failed (${res.status})`)
		}

		const timelapse: TimelapseResponse = await res.json()
		emit('timelapse-created', timelapse)
		dialogOpen.value = false
	} catch (err) {
		submitError.value = err instanceof Error ? err.message : 'An unexpected error occurred.'
	} finally {
		isSubmitting.value = false
	}
}

onMounted(async () => {
	cameras.value = await fetch('/api/v1/cameras').then(res => res.json())
})
</script>

<template>
	<Dialog v-model:open="dialogOpen">
		<DialogTrigger as-child>
			<Button>Create Timelapse</Button>
		</DialogTrigger>
		<DialogContent class="sm:max-w-[500px]">
			<form @submit.prevent="handleSubmit">
				<DialogHeader>
					<DialogTitle>Create Timelapse</DialogTitle>
					<DialogDescription>
						Configure your timelapse and choose whether to start it now or queue it for later.
					</DialogDescription>
				</DialogHeader>

				<div v-if="cameras.length == 0" class="flex items-center gap-3 px-4 py-3 mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-sm text-amber-300">
					<PhWarning variant="duotone" :size="18" class="shrink-0 text-amber-400" />
					<span>You must add a camera connection in the 'Settings' page before creating a timelapse!</span>

				</div>

				<FieldSet class="mt-4">
					<FieldGroup>
						<!-- Camera -->
						<Field>
							<FieldLabel for="camera">Camera</FieldLabel>
							<Select v-model="form.camera_id">
								<SelectTrigger id="camera">
									<SelectValue placeholder="Select a camera" />
								</SelectTrigger>
								<SelectContent>
									<SelectItem
										v-for="camera in cameras"
										:key="camera.id"
										:value="camera.id"
									>
										{{ camera.name }}
									</SelectItem>
								</SelectContent>
							</Select>
						</Field>

						<!-- Name -->
						<Field>
							<FieldLabel for="name">Name</FieldLabel>
							<Input id="name" type="text" v-model="form.name" placeholder="My Timelapse" />
						</Field>

						<!-- Interval -->
						<Field>
							<FieldLabel for="interval_seconds">Interval</FieldLabel>
							<div class="flex items-center gap-2">
								<Input
									id="interval_seconds"
									type="number"
									min="1"
									v-model.number="form.interval_seconds"
									class="w-28"
								/>
								<span class="text-sm text-muted-foreground">seconds between frames</span>
							</div>
						</Field>
					</FieldGroup>
				</FieldSet>

				<Separator class="my-4" />

				<FieldSet>
					<FieldGroup>
						<!-- Start immediately toggle -->
						<Field>
							<div class="flex items-center justify-between">
								<div>
									<FieldLabel>Start immediately</FieldLabel>
									<FieldDescription class="mt-0.5">
										Begin capturing frames as soon as the timelapse is created.
									</FieldDescription>
								</div>
								<Switch v-model="startImmediately" />
							</div>
							<div v-if="!startImmediately" class="mt-2">
								<Label for="scheduled_start" class="text-sm text-muted-foreground mb-1 block">
									Starts at
								</Label>
								<Input
									id="scheduled_start"
									type="datetime-local"
									v-model="scheduledStart"
								/>
							</div>
						</Field>

						<!-- Run indefinitely toggle -->
						<Field>
							<div class="flex items-center justify-between">
								<div>
									<FieldLabel>Run indefinitely</FieldLabel>
									<FieldDescription class="mt-0.5">
										Keep capturing until the timelapse is manually stopped.
									</FieldDescription>
								</div>
								<Switch v-model="isIndefinite" />
							</div>
							<div v-if="!isIndefinite" class="mt-2">
								<Label for="scheduled_end" class="text-sm text-muted-foreground mb-1 block">
									Ends at
								</Label>
								<Input
									id="scheduled_end"
									type="datetime-local"
									v-model="scheduledEnd"
								/>
							</div>
						</Field>
					</FieldGroup>
				</FieldSet>

				<DialogFooter class="flex-col items-start gap-2 sm:flex-row sm:items-center pt-4">
					<p v-if="submitError" class="text-sm text-destructive flex-1">{{ submitError }}</p>
					<div class="flex gap-2 sm:ml-auto">
						<DialogClose as-child>
							<Button type="button" variant="outline" :disabled="isSubmitting">Cancel</Button>
						</DialogClose>
						<Button type="submit" :disabled="isSubmitting">
							<span v-if="isSubmitting">Saving...</span>
							<span v-else>{{ startImmediately ? 'Create & Start' : 'Queue Timelapse' }}</span>
						</Button>
					</div>
				</DialogFooter>
			</form>
		</DialogContent>
	</Dialog>
</template>
