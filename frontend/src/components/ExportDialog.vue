<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
	Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ButtonGroup } from '@/components/ui/button-group'
import { Input } from '@/components/ui/input'
import {
	Field, FieldError, FieldGroup, FieldLabel, FieldSet,
} from '@/components/ui/field'
import FieldDescription from '@/components/ui/field/FieldDescription.vue'
import {
	Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import Separator from '@/components/ui/separator/Separator.vue'
import { PhFilmSlate, PhSpinner } from '@phosphor-icons/vue'
import type { ExportJobResponse, ExportRequest, OutputFormat, ExportResolution } from '@/types'
import { startExport } from '@/api/export'

const props = defineProps<{
	timelapseId: number
	frameCount: number
}>()

const emit = defineEmits<{
	jobStarted: [job: ExportJobResponse]
}>()

// Dialog state
const open = ref(false)
const isSubmitting = ref(false)
const submitError = ref<string | null>(null)

// Basic tab
const outputFormat = ref<OutputFormat>('webm')
const resolution = ref<ExportResolution>('original')
const customResolution = ref('')
const customResTouched = ref(false)
const crf = ref<number[]>([28])

// Speed mode
const speedMode = ref<'fps' | 'duration'>('fps')
const outputFps = ref(30)
const durationPreset = ref<number | 'custom' | null>(null)
const customDurationSeconds = ref<number>(30)

// Filters tab
const smoothing = ref<'none' | 'blend' | 'interpolate'>('none')
const stabilization = ref(false)
const denoising = ref(false)
const colorCorrection = ref<'none' | 'auto' | 'manual'>('none')

// prevent ToggleGroup from allowing undefined state
watch(smoothing, (val) => { if (val === undefined) smoothing.value = 'none' })
watch(colorCorrection, (val) => { if (val === undefined) colorCorrection.value = 'none' })

const brightness = ref<number[]>([0])      // -100 to 100
const contrast = ref<number[]>([100])      // 50 to 200
const saturation = ref<number[]>([100])    // 0 to 200

// Computed
const customResError = computed(() => {
	if (resolution.value !== 'custom' || !customResTouched.value) return ''
	if (!customResolution.value.trim()) return 'Resolution is required'
	if (!/^\d+x\d+$/.test(customResolution.value)) return 'Format must be WxH (e.g. 1920x1080)'
	return ''
})

const effectiveFps = computed(() => {
	if (speedMode.value === 'duration') {
		let secs: number | null = null
		if (durationPreset.value === 'custom') {
			secs = customDurationSeconds.value
		} else if (typeof durationPreset.value === 'number') {
			secs = durationPreset.value
		}
		if (secs !== null && secs > 0) {
			return Math.max(1, Math.round(props.frameCount / secs))
		}
	}
	return outputFps.value
})

const estimatedSeconds = computed(() => {
	const fps = effectiveFps.value
	if (!fps || fps <= 0) return 0
	return Math.round(props.frameCount / fps)
})

const smoothingDescription = computed(() => {
	if (smoothing.value === 'blend') return 'Simple fade between frames — fast to export'
	if (smoothing.value === 'interpolate') return 'Creates new in-between frames for buttery motion — slower export'
	return 'No additional motion smoothing applied'
})

const crfDisplay = computed(() => crf.value[0])
const brightnessDisplay = computed(() => brightness.value[0])
const contrastDisplay = computed(() => ((contrast.value[0] ?? 100) / 100).toFixed(2))
const saturationDisplay = computed(() => ((saturation.value[0] ?? 100) / 100).toFixed(2))

const activeFilterCount = computed(() => {
	let count = 0
	if (smoothing.value !== 'none') count++
	if (stabilization.value) count++
	if (denoising.value) count++
	if (colorCorrection.value !== 'none') count++
	return count
})

// Reset on close
watch(open, (isOpen) => {
	if (!isOpen) {
		outputFormat.value = 'webm'
		resolution.value = 'original'
		customResolution.value = ''
		customResTouched.value = false
		crf.value = [28]
		submitError.value = null

		speedMode.value = 'fps'
		outputFps.value = 30
		durationPreset.value = null
		customDurationSeconds.value = 30

		smoothing.value = 'none'
		stabilization.value = false
		denoising.value = false
		colorCorrection.value = 'none'
		brightness.value = [0]
		contrast.value = [100]
		saturation.value = [100]
	}
})

async function handleSubmit() {
	customResTouched.value = true
	if (customResError.value) return

	isSubmitting.value = true
	submitError.value = null
	try {
		const targetDuration =
			speedMode.value === 'duration'
				? (durationPreset.value === 'custom' ? customDurationSeconds.value : durationPreset.value as number) || undefined
				: undefined

		const payload: ExportRequest = {
			output_format:     outputFormat.value,
			output_fps:        effectiveFps.value,
			resolution:        resolution.value,
			custom_resolution: resolution.value === 'custom' ? customResolution.value : undefined,
			crf:               crf.value[0] ?? 28,
			smoothing:         smoothing.value !== 'none' ? smoothing.value : undefined,
			target_duration:   targetDuration,
			stabilization:     stabilization.value || undefined,
			denoising:         denoising.value || undefined,
			color_correction:  colorCorrection.value !== 'none' ? colorCorrection.value : undefined,
			brightness:        colorCorrection.value === 'manual' ? (brightness.value[0] ?? 0) / 100 : undefined,
			contrast:          colorCorrection.value === 'manual' ? (contrast.value[0] ?? 100) / 100 : undefined,
			saturation:        colorCorrection.value === 'manual' ? (saturation.value[0] ?? 100) / 100 : undefined,
		}

		const result = await startExport(props.timelapseId, payload)
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

		<DialogContent class="sm:max-w-xl">
			<DialogHeader>
				<DialogTitle>Export Timelapse</DialogTitle>
			</DialogHeader>

			<Tabs default-value="basic" class="mt-1">
				<TabsList class="w-full">
					<TabsTrigger value="basic" class="flex-1">Basic</TabsTrigger>
					<TabsTrigger value="filters" class="flex-1">
						Filters
						<span
							v-if="activeFilterCount > 0"
							class="ml-1.5 inline-flex items-center justify-center rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-semibold text-primary-foreground leading-none"
						>{{ activeFilterCount }}</span>
					</TabsTrigger>
				</TabsList>

				<!-- Basic Tab -->
				<TabsContent value="basic">
					<FieldSet class="py-3 px-0.5">
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
								<Field :class="resolution === 'custom' ? 'basis-1/2' : 'basis-full'">
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
								<Field v-if="resolution === 'custom'" class="basis-1/2">
									<FieldLabel>Custom (W×H)</FieldLabel>
									<Input
										v-model="customResolution"
										placeholder="e.g. 1440x900"
										@blur="customResTouched = true"
									/>
									<FieldError :errors="customResError ? [customResError] : []" />
								</Field>
							</div>

							<!-- Speed mode toggle -->
							<Field>
								<FieldLabel>Speed</FieldLabel>
								<ButtonGroup class="w-full">
									<Button
										class="flex-1"
										:variant="speedMode === 'fps' ? 'default' : 'outline'"
										type="button"
										@click="speedMode = 'fps'"
									>FPS</Button>
									<Button
										class="flex-1"
										:variant="speedMode === 'duration' ? 'default' : 'outline'"
										type="button"
										@click="speedMode = 'duration'"
									>Duration</Button>
								</ButtonGroup>

								<!-- FPS mode -->
								<div v-if="speedMode === 'fps'" class="mt-2">
									<Input
										v-model.number="outputFps"
										type="number"
										min="1"
										max="120"
										placeholder="30"
									/>
									<FieldDescription class="mt-1">Frames per second in the output video</FieldDescription>
								</div>

								<!-- Duration mode -->
								<div v-else class="mt-2 space-y-2">
									<Select v-model="durationPreset">
										<SelectTrigger class="w-full">
											<SelectValue placeholder="Select target length…" />
										</SelectTrigger>
										<SelectContent>
											<SelectItem :value="10">10 seconds</SelectItem>
											<SelectItem :value="15">15 seconds</SelectItem>
											<SelectItem :value="30">30 seconds</SelectItem>
											<SelectItem :value="60">1 minute</SelectItem>
											<SelectItem :value="120">2 minutes</SelectItem>
											<SelectItem :value="300">5 minutes</SelectItem>
											<SelectItem value="custom">Custom…</SelectItem>
										</SelectContent>
									</Select>
									<div v-if="durationPreset === 'custom'" class="flex items-center gap-2">
										<Input
											v-model.number="customDurationSeconds"
											type="number"
											min="1"
											placeholder="seconds"
											class="w-32"
										/>
										<span class="text-sm text-muted-foreground">seconds</span>
									</div>
									<FieldDescription>FPS is calculated to fit your frame count into the target duration</FieldDescription>
								</div>
							</Field>

							<!-- Quality (CRF) -->
							<Field>
								<div class="flex items-center justify-between mb-2">
									<FieldLabel class="mb-0">Quality (CRF)</FieldLabel>
									<span class="text-sm font-medium tabular-nums">{{ crfDisplay }}</span>
								</div>
								<Slider
									v-model="crf"
									:min="0"
									:max="63"
									:step="1"
								/>
								<div class="flex justify-between mt-1">
									<span class="text-[11px] text-muted-foreground">0 — best</span>
									<span class="text-[11px] text-muted-foreground">63 — smallest</span>
								</div>
							</Field>

						</FieldGroup>
					</FieldSet>
				</TabsContent>

				<!-- Filters Tab -->
				<TabsContent value="filters">
					<FieldSet class="py-3 px-0.5">
						<FieldGroup class="gap-5">

							<!-- Smoothing -->
							<Field>
								<FieldLabel>Smoothing</FieldLabel>
								<ToggleGroup
									v-model="smoothing"
									type="single"
									variant="outline"
									class="w-full"
								>
									<ToggleGroupItem value="none" class="flex-1">None</ToggleGroupItem>
									<ToggleGroupItem value="blend" class="flex-1">Frame Blend</ToggleGroupItem>
									<ToggleGroupItem value="interpolate" class="flex-1">Interpolate</ToggleGroupItem>
								</ToggleGroup>
								<FieldDescription>{{ smoothingDescription }}</FieldDescription>
							</Field>

							<Separator />

							<!-- Stabilization -->
							<Field>
								<div class="flex items-center justify-between">
									<div>
										<FieldLabel class="mb-0">Stabilization</FieldLabel>
										<FieldDescription>Fix shaky footage (slower export)</FieldDescription>
									</div>
									<Switch v-model="stabilization" />
								</div>
							</Field>

							<!-- Denoising -->
							<Field>
								<div class="flex items-center justify-between">
									<div>
										<FieldLabel class="mb-0">Denoise</FieldLabel>
										<FieldDescription>Reduce noise and grain in footage</FieldDescription>
									</div>
									<Switch v-model="denoising" />
								</div>
							</Field>

							<Separator />

							<!-- Color Correction -->
							<Field>
								<FieldLabel>Color Correction</FieldLabel>
								<ToggleGroup
									v-model="colorCorrection"
									type="single"
									variant="outline"
									class="w-full"
								>
									<ToggleGroupItem value="none" class="flex-1">None</ToggleGroupItem>
									<ToggleGroupItem value="auto" class="flex-1">Auto</ToggleGroupItem>
									<ToggleGroupItem value="manual" class="flex-1">Manual</ToggleGroupItem>
								</ToggleGroup>

								<!-- Auto description -->
								<FieldDescription v-if="colorCorrection === 'auto'">
									Applies histogram equalization to balance exposure automatically
								</FieldDescription>

								<!-- Manual sliders -->
								<div v-if="colorCorrection === 'manual'" class="mt-3 space-y-4 pl-3 border-l-2 border-muted">
									<!-- Brightness -->
									<div>
										<div class="flex items-center justify-between mb-2">
											<span class="text-sm font-medium">Brightness</span>
											<span class="text-sm tabular-nums text-muted-foreground">{{ brightnessDisplay }}</span>
										</div>
										<Slider v-model="brightness" :min="-100" :max="100" :step="1" />
										<div class="flex justify-between mt-1">
											<span class="text-[11px] text-muted-foreground">-100</span>
											<span class="text-[11px] text-muted-foreground">+100</span>
										</div>
									</div>

									<!-- Contrast -->
									<div>
										<div class="flex items-center justify-between mb-2">
											<span class="text-sm font-medium">Contrast</span>
											<span class="text-sm tabular-nums text-muted-foreground">{{ contrastDisplay }}×</span>
										</div>
										<Slider v-model="contrast" :min="50" :max="200" :step="1" />
										<div class="flex justify-between mt-1">
											<span class="text-[11px] text-muted-foreground">0.50×</span>
											<span class="text-[11px] text-muted-foreground">2.00×</span>
										</div>
									</div>

									<!-- Saturation -->
									<div>
										<div class="flex items-center justify-between mb-2">
											<span class="text-sm font-medium">Saturation</span>
											<span class="text-sm tabular-nums text-muted-foreground">{{ saturationDisplay }}×</span>
										</div>
										<Slider v-model="saturation" :min="0" :max="200" :step="1" />
										<div class="flex justify-between mt-1">
											<span class="text-[11px] text-muted-foreground">0.00×</span>
											<span class="text-[11px] text-muted-foreground">2.00×</span>
										</div>
									</div>
								</div>
							</Field>

						</FieldGroup>
					</FieldSet>
				</TabsContent>
			</Tabs>

			<DialogFooter class="flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
				<p class="text-xs text-muted-foreground order-last sm:order-first">
					{{ frameCount }} frames → ~{{ estimatedSeconds }}s at {{ effectiveFps }} fps
				</p>
				<p v-if="submitError" class="text-xs text-destructive text-right">{{ submitError }}</p>
				<div class="flex gap-2 justify-end">
					<Button variant="outline" @click="open = false">Cancel</Button>
					<Button :disabled="isSubmitting" @click="handleSubmit">
						<PhSpinner v-if="isSubmitting" weight="duotone" class="animate-spin" />
						{{ isSubmitting ? 'Exporting…' : 'Start Export' }}
					</Button>
				</div>
			</DialogFooter>
		</DialogContent>
	</Dialog>
</template>
