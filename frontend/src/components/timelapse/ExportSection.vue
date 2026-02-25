<script setup lang="ts">
import { ref, onMounted, onUnmounted, type Component } from 'vue'
import { getExportsForTimelapse, getExportStatus, downloadExport } from '@/api/export'
import type { ExportJobResponse, ExportStatus } from '@/types'
import Collapsible from '../ui/collapsible/Collapsible.vue'
import CollapsibleTrigger from '../ui/collapsible/CollapsibleTrigger.vue'
import CollapsibleContent from '../ui/collapsible/CollapsibleContent.vue'
import Button from '../ui/button/Button.vue'
import { PhCaretDown, PhCheckCircle, PhDownloadSimple, PhFilmSlate, PhSpinner, PhTrash, PhWarning } from '@phosphor-icons/vue'
import { formatDuration } from 'date-fns'

const props = defineProps<{
	timelapseId: number,
}>()

const statusBadge: Record<ExportStatus, { label: string, class: string, icon: Component }> = {
	pending:   { label: 'Pending',   class: 'bg-zinc-700/80 text-zinc-300',      icon: PhSpinner },
	running:   { label: 'Running',   class: 'bg-cyan-800/80 text-cyan-200',      icon: PhSpinner },
	completed: { label: 'Completed', class: 'bg-emerald-800/80 text-emerald-200', icon: PhCheckCircle },
	error:     { label: 'Error',     class: 'bg-red-800/80 text-red-200',        icon: PhWarning },
}

const exportJobs = ref<ExportJobResponse[]>([])
const openStates = ref<Record<number, boolean>>({})
let exportPollTimer: ReturnType<typeof setInterval> | null = null

function onJobStarted(job: ExportJobResponse) {
	exportJobs.value.unshift(job)
	startExportPolling()
}

function startExportPolling() {
	if (exportPollTimer !== null) return
	exportPollTimer = setInterval(async () => {
		const active = exportJobs.value.filter(
			j => j.status === 'pending' || j.status === 'running'
		)
		if (active.length === 0) {
			clearInterval(exportPollTimer!)
			exportPollTimer = null
			return
		}
		for (const job of active) {
			try {
				const updated = await getExportStatus(job.id)
				const idx = exportJobs.value.findIndex(j => j.id === job.id)
				if (idx !== -1) exportJobs.value[idx] = updated
			} catch {
				// network hiccup — keep polling
			}
		}
	}, 1000)
}

async function downloadExportFile(job: ExportJobResponse) {
	try {
		const blob = await downloadExport(job.id)
		const url = URL.createObjectURL(blob)
		const a = document.createElement('a')
		a.href = url
		a.download = job.output_file ?? `timelapse_${job.timelapse_id}.${job.output_format}`
		a.click()
		URL.revokeObjectURL(url)
	} catch (err) {
		console.error('Download failed:', err)
	}
}

onMounted(async () => {
	try {
		exportJobs.value = await getExportsForTimelapse(props.timelapseId)
		if (exportJobs.value.some(j => j.status === 'pending' || j.status === 'running')) {
			startExportPolling()
		}
	} catch {
		// non-fatal — exports section simply stays empty
	}
})

onUnmounted(() => {
	if (exportPollTimer !== null) {
		clearInterval(exportPollTimer)
		exportPollTimer = null
	}
})

defineExpose({ onJobStarted })
</script>

<template>
	<div v-if="exportJobs.length > 0" class="border rounded-lg bg-zinc-100 dark:bg-zinc-900 overflow-hidden">
		<!-- Section header -->
		<div class="px-4 pt-3 pb-3 flex items-center gap-2">
			<PhFilmSlate variant="duotone" :size="16" class="text-zinc-400" />
			<h2 class="text-sm font-medium">Exports</h2>
		</div>

		<!-- Job list -->
		<div class="px-2 pb-2 space-y-2 max-h-80 overflow-y-auto">
			<Collapsible
				v-for="job in exportJobs"
				:key="job.id"
				:open="openStates[job.id] ?? false"
				@update:open="openStates[job.id] = $event"
				class="rounded-md border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 overflow-hidden"
			>
				<!-- Always-visible trigger row -->
				<CollapsibleTrigger as-child>
					<button class="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-zinc-50 dark:hover:bg-zinc-700/50 transition-colors cursor-pointer">
						<div class="flex items-center gap-3">
							<span class="text-sm font-semibold uppercase tracking-wide">{{ job.output_format }}</span>
							<span class="text-xs text-muted-foreground">{{ job.output_fps }} fps · {{ job.resolution }}</span>
						</div>

						<div class="flex items-center gap-2">
							<div
								class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium"
								:class="statusBadge[job.status].class"
							>
								<component
									:is="statusBadge[job.status].icon"
									:size="12"
									:class="{ 'animate-spin': job.status === 'pending' || job.status === 'running' }"
								/>
								{{ statusBadge[job.status].label }}
							</div>
							<PhCaretDown
								:size="14"
								class="text-zinc-400 transition-transform duration-200 shrink-0"
								:class="{ 'rotate-180': openStates[job.id] }"
							/>
						</div>

						<!-- Progress bar (always visible while active) -->
						<div v-if="job.status === 'pending' || job.status === 'running'" class="px-3 pb-2.5 space-y-1">
							<div class="w-full bg-zinc-200 dark:bg-zinc-700 rounded-full h-1 overflow-hidden">
								<div
									class="bg-primary h-1 rounded-full transition-all duration-500"
									:style="{ width: `${job.progress_pct}%` }"
								/>
							</div>
							<p class="text-xs text-muted-foreground">{{ job.frames_done }} / {{ job.total_frames }} frames</p>
						</div>
					</button>
				</CollapsibleTrigger>

				<!-- Collapsible details -->
				<CollapsibleContent class="border-t border-zinc-200 dark:border-zinc-700">
					<div class="px-3 py-2.5 space-y-3">
						<!-- Stats grid -->
						<div class="grid grid-cols-3 gap-3 text-xs">
							<div>
								<p class="text-muted-foreground">CRF</p>
								<p class="font-medium">{{ job.crf }}</p>
							</div>
							<div>
								<p class="text-muted-foreground">Length</p>
								<p class="font-medium">~{{ formatDuration({ seconds: Math.round(job.total_frames / job.output_fps) }) }}</p>
								<p class="text-muted-foreground">({{ job.total_frames }} frames @ {{ job.output_fps }}fps)</p>
							</div>
							<div>
								<p class="text-muted-foreground">Created</p>
								<p class="font-medium">{{ new Date(job.created_at).toLocaleDateString() }}</p>
							</div>
						</div>

						<!-- Error message -->
						<pre
							v-if="job.status === 'error' && job.error_message"
							class="text-xs bg-zinc-200 dark:bg-zinc-950 rounded p-2 overflow-auto max-h-24 text-red-400 whitespace-pre-wrap break-all"
						>{{ job.error_message }}</pre>

						<!-- Actions -->
						<div v-if="job.status === 'completed'" class="flex items-center gap-2">
							<Button size="sm" variant="outline" @click="downloadExportFile(job)">
								<PhDownloadSimple variant="duotone" :size="14" />
								Download
							</Button>
							<!-- TODO: Implement delete -->
							<Button size="sm" variant="destructive">
								<PhTrash variant="duotone" :size="14" />
								<span class="sr-only">Delete export</span>
							</Button>
						</div>
					</div>
				</CollapsibleContent>
			</Collapsible>
		</div>
	</div>
</template>
