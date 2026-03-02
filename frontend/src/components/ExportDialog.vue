<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
	Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
	Field,
	FieldError,
	FieldGroup,
	FieldLabel,
	FieldSet,
} from '@/components/ui/field'
import {
	Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { PhFilmSlate, PhSpinner } from '@phosphor-icons/vue'
import type { ExportJobResponse, OutputFormat, ExportResolution } from '@/types'
import { startExport } from '@/api/export'
import FieldDescription from './ui/field/FieldDescription.vue'

const props = defineProps<{
	timelapseId: number
	frameCount: number
}>()

const emit = defineEmits<{
	jobStarted: [job: ExportJobResponse]
}>()

const open = ref(false)
const isSubmitting = ref(false)
const submitError = ref<string | null>(null)

const outputFormat = ref<OutputFormat>('webm')
const outputFps = ref(30)
const resolution = ref<ExportResolution>('original')
const customResolution = ref('')
const crf = ref(28)

const estimatedSeconds = computed(() => Math.round(props.frameCount / outputFps.value))

const customResTouched = ref(false)

const customResError = computed(() => {
	if (resolution.value !== 'custom' || !customResTouched.value) return ''
	if (!customResolution.value.trim()) return 'Resolution is required'
	if (!/^\d+x\d+$/.test(customResolution.value)) return 'Format must be WxH (e.g. 1920x1080)'
	return ''
})

watch(open, (isOpen) => {
	if (isOpen) {
		outputFormat.value = 'webm'
		outputFps.value = 30
		resolution.value = 'original'
		customResolution.value = ''
		crf.value = 28
		submitError.value = null
		customResTouched.value = false
	}
})

async function handleSubmit() {
	customResTouched.value = true
	if (customResError.value) return

	isSubmitting.value = true
	submitError.value = null
	try {
		const result = await startExport(props.timelapseId, {
			output_format: outputFormat.value,
			output_fps: outputFps.value,
			resolution: resolution.value,
			custom_resolution: resolution.value === 'custom' ? customResolution.value : null,
			crf: crf.value,
		})
		emit('jobStarted', result)
		open.value = false
	} catch (err) {
		submitError.value = err instanceof Error ? err.message : 'Failed to start export'
	} finally {
		isSubmitting.value = false
	}
}
</script>

<template>
	<Dialog v-model:open="open">
		<DialogTrigger as-child>
			<Button variant="outline">
				<PhFilmSlate weight="duotone" />
				Export
			</Button>
		</DialogTrigger>

		<DialogContent class="sm:max-w-md">
			<DialogHeader>
				<DialogTitle>Export Timelapse</DialogTitle>
			</DialogHeader>

			<FieldSet class="py-2">
				<FieldGroup class="gap-5">
					<!-- Format -->
					<Field>
						<FieldLabel>Format</FieldLabel>
						<Select v-model="outputFormat">
							<SelectTrigger class="w-full">
								<SelectValue />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="webm">WebM (VP9)</SelectItem>
								<SelectItem value="mp4">MP4 (H.264)</SelectItem>
							</SelectContent>
						</Select>
					</Field>

					<!-- Resolution -->
					<div class="flex gap-3">
						<Field :class="resolution === 'custom' ? ' basis-1/2' : 'basis-full'">
							<FieldLabel>Resolution</FieldLabel>
							<Select v-model="resolution">
								<SelectTrigger class="w-full">
									<SelectValue />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="original">Original</SelectItem>
									<SelectItem value="1920x1080">1920 × 1080</SelectItem>
									<SelectItem value="1280x720">1280 × 720</SelectItem>
									<SelectItem value="640x360">640 × 360</SelectItem>
									<SelectItem value="custom">Custom…</SelectItem>
								</SelectContent>
							</Select>
						</Field>

						<!-- Custom resolution -->
						<Field v-if="resolution === 'custom'">
							<FieldLabel>Custom resolution (W×H)</FieldLabel>
							<Input v-model="customResolution" placeholder="e.g. 1440x900" @blur="customResTouched = true" />
							<FieldError :errors="customResError ? [customResError] : []" />
						</Field>
					</div>
					

					<div class="grid grid-cols-2 gap-3">
						<!-- FPS -->
						<Field>
							<FieldLabel>Frames per second</FieldLabel>
							<Input v-model.number="outputFps" type="number" min="1" max="120" />
						</Field>

						<!-- CRF -->
						<Field>
							<FieldLabel>Quality <span class="text-xs text-muted-foreground">(lower = better)</span></FieldLabel>
							<Input v-model.number="crf" type="number" min="0" max="63" />
						</Field>
					</div>
					

					<!-- Estimate -->
					<p class="text-xs text-muted-foreground">
						{{ frameCount }} frames at {{ outputFps }} fps ≈ {{ estimatedSeconds }}s video
					</p>

					<!-- Inline error -->
					<p v-if="submitError" class="text-xs text-red-400">{{ submitError }}</p>
				</FieldGroup>
			</FieldSet>

			<DialogFooter>
				<Button variant="outline" @click="open = false">Cancel</Button>
				<Button :disabled="isSubmitting" @click="handleSubmit">
					<PhSpinner v-if="isSubmitting" variant="duotone" class="animate-spin" />
					{{ isSubmitting ? 'Exporting...' : 'Start Export' }}
				</Button>
			</DialogFooter>
		</DialogContent>
	</Dialog>
</template>
