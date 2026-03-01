<script setup lang="ts">
import { ref, onMounted, onUnmounted, type Component } from 'vue'
import { getExportsForTimelapse, getExportStatus, downloadExport, deleteExport } from '@/api/export'
import type { ExportJobResponse, ExportStatus } from '@/types'
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '../ui/collapsible'
import {
	AlertDialog, AlertDialogContent,
	AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
	AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '@/components/ui/alert-dialog'
import Button from '../ui/button/Button.vue'
import { PhCaretDown, PhCheckCircle, PhDownloadSimple, PhFilmSlate, PhSpinner, PhTrash, PhWarning } from '@phosphor-icons/vue'
import { formatBytes, formatInterval } from '@/lib/format'

const props = defineProps<{
	timelapseId: number,
	storagePath?: string,
}>()

const emit = defineEmits<{
	(e: 'error', message: string): void
}>()

const statusBadge: Record<ExportStatus, { label: string, class: string, icon: Component }> = {
	pending:   { label: 'Pending',   class: 'bg-zinc-700/80 text-zinc-300',      icon: PhSpinner },
	running:   { label: 'Running',   class: 'bg-cyan-800/80 text-cyan-200',      icon: PhSpinner },
	completed: { label: 'Completed', class: 'bg-emerald-800/80 text-emerald-200', icon: PhCheckCircle },
	error:     { label: 'Error',     class: 'bg-red-800/80 text-red-200',        icon: PhWarning },
}

const exportJobs = ref<ExportJobResponse[]>([])
const openStates = ref<Record<number, boolean>>({})
const exportToDelete = ref<ExportJobResponse | null>(null)

// Smarter polling logic with 'exponential backoff' on errors, to avoid curb-stomping the server while its already struggling
let exportPollTimer: ReturnType<typeof setTimeout> | null = null
let pollErrorCount = 0
const MAX_POLL_ERRORS = 5
const BASE_POLL_INTERVAL = 1000

function schedulePoll(delayMs: number) {
	exportPollTimer = setTimeout(pollOnce, delayMs)
}

async function pollOnce() {
	const active = exportJobs.value.filter(j => j.status === 'pending' || j.status === 'running')
	if (active.length === 0) {
		exportPollTimer = null
		pollErrorCount = 0
		return
	}
	let hadError = false
	for (const job of active) {
		try {
			const updated = await getExportStatus(job.id)
			const idx = exportJobs.value.findIndex(j => j.id === job.id)
			if (idx !== -1) exportJobs.value[idx] = updated
			pollErrorCount = 0
		} catch {
			hadError = true
		}
	}
	if (hadError) {
		pollErrorCount++
		if (pollErrorCount >= MAX_POLL_ERRORS) {
			exportPollTimer = null
			emit('error', 'Lost connection to server while polling exports. Refresh to resume.')
			return
		}
		const backoff = Math.min(BASE_POLL_INTERVAL * 2 ** pollErrorCount, 30000)
		schedulePoll(backoff)
	} else {
		schedulePoll(BASE_POLL_INTERVAL)
	}
}

function onJobStarted(job: ExportJobResponse) {
	exportJobs.value.unshift(job)
	startExportPolling()
}

function startExportPolling() {
	if (exportPollTimer !== null) return
	schedulePoll(BASE_POLL_INTERVAL)
}

async function deleteExportJob() {
	if (!exportToDelete.value) return
	try {
		await deleteExport(exportToDelete.value.id)
		exportJobs.value = exportJobs.value.filter(j => j.id !== exportToDelete.value?.id)
		exportToDelete.value = null
	} catch (err) {
		emit('error', `Failed to delete export #${exportToDelete.value?.id}. (${err instanceof Error ? err.message : 'Unknown error'})`)
		exportToDelete.value = null
	}
}

async function downloadExportFile(job: ExportJobResponse) {
	try {
		const blob = await downloadExport(job.id)
		const url = URL.createObjectURL(blob)
		const a = document.createElement('a')
		a.href = url
		a.download = job.output_file ?? `timelapse_${job.timelapse_id}_${job.id}.${job.output_format}`
		a.click()
		URL.revokeObjectURL(url)
	} catch (err) {
		emit('error', `Failed to download export #${job.id}. (${err instanceof Error ? err.message : 'Unknown error'})`)
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
		clearTimeout(exportPollTimer)
		exportPollTimer = null
	}
})

defineExpose({ onJobStarted })
</script>

<template>
	<div v-if="exportJobs.length > 0" class="h-full flex flex-col border rounded-lg bg-zinc-100 dark:bg-zinc-900 overflow-hidden">
		<!-- Section header -->
		<div class="shrink-0 px-4 pt-3 pb-3 flex items-center gap-2">
			<PhFilmSlate variant="duotone" :size="16" class="text-zinc-400" />
			<h2 class="text-sm font-medium">Exports</h2>
		</div>

		<!-- Job list -->
		<div class="flex-1 min-h-0 px-2 pb-2 space-y-2 overflow-y-auto">
			<Collapsible
				v-for="job in exportJobs"
				:key="job.id"
				:open="openStates[job.id] ?? false"
				@update:open="openStates[job.id] = $event"
				class="rounded-md border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 overflow-hidden"
			>
				<!-- Always-visible trigger row -->
				<CollapsibleTrigger as-child>
					<button class="w-full flex flex-col px-3 py-2.5 text-left hover:bg-zinc-50 dark:hover:bg-zinc-700/50 transition-colors cursor-pointer">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-3">
								<span class="text-sm font-semibold uppercase tracking-wide">{{ job.output_format }}</span>
								<span class="text-xs text-muted-foreground">{{ job.output_fps }} fps · {{ job.resolution }}</span>
							</div>

							<div class="flex items-center gap-2">
								<span v-if="job.file_size_bytes" class="text-xs text-foreground">
									{{ formatBytes(job.file_size_bytes) }}
								</span>
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
						</div>
						
						<!-- Progress bar (always visible while active) -->
						<div v-if="job.status === 'pending' || job.status === 'running'" class="pt-2 space-y-1">
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
								<p class="font-medium">~{{ formatInterval(Math.round(job.total_frames / job.output_fps)) }}</p>
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

						<!-- Actions: show for completed and error states -->
						<div v-if="job.status === 'completed' || job.status === 'error'" class="flex items-center justify-between gap-2">
							<Button v-if="job.status === 'completed'" size="sm" variant="outline" @click="downloadExportFile(job)">
								<PhDownloadSimple variant="duotone" :size="14" />
								Download
							</Button>
							<Button size="sm" variant="destructive" @click="exportToDelete = job">
								<PhTrash variant="duotone" :size="14" />
								<span class="sr-only">Delete export</span>
							</Button>
						</div>
					</div>
				</CollapsibleContent>
			</Collapsible>
		</div>

		<AlertDialog :open="exportToDelete !== null">
			<AlertDialogContent>
				<AlertDialogHeader>
					<AlertDialogTitle>Delete export #{{exportToDelete?.id }}'?</AlertDialogTitle>
					<AlertDialogDescription>
						Are you sure you want to delete this export?<br>
						<strong>This action cannot be undone.</strong>
						<pre class="mt-2 px-2 py-1 text-xs bg-zinc-800/60 rounded-sm text-blue-300">{{storagePath}}/exports/{{ exportToDelete?.output_file }}</pre>
						<span class="text-xs text-muted-foreground">(if job failed, file might not exist)</span>
					</AlertDialogDescription>
				</AlertDialogHeader>
				<AlertDialogFooter>
					<AlertDialogCancel @click="exportToDelete = null">Cancel</AlertDialogCancel>
					<AlertDialogAction @click="deleteExportJob" class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
						Delete
					</AlertDialogAction>
				</AlertDialogFooter>
			</AlertDialogContent>
		</AlertDialog>
	</div>
</template>
