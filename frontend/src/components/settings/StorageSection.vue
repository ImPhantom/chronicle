<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { PhCaretDown, PhHardDrive, PhSpinner } from '@phosphor-icons/vue'
import type { StorageStats, TimelapseResponse, TimelapseStorageItem } from '@/types'
import { getStorageStats } from '@/api/settings';
import { formatBytes } from '@/lib/format';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';

const props = defineProps<{
	loading: boolean,
	timelapses: TimelapseResponse[],
}>()

const emit = defineEmits<{
	(e: 'error', message: string): void
}>()

const storageStats = ref<StorageStats | null>(null)
const storageOpen = ref(false)

const breakdownMap = computed(() => {
	const map = new Map<number, TimelapseStorageItem>()
	if (storageStats.value) {
		for (const item of storageStats.value.timelapse_breakdown) {
			map.set(item.timelapse_id, item)
		}
	}
	return map
})

const showAllTimelapses = ref(false)
const sortedTimelapses = computed(() =>
	[...props.timelapses].sort((a, b) => {
		const bItem = breakdownMap.value.get(b.id)
		const aItem = breakdownMap.value.get(a.id)
		const bTotal = (bItem?.frames_size_bytes ?? b.size_bytes) + (bItem?.exports_size_bytes ?? 0)
		const aTotal = (aItem?.frames_size_bytes ?? a.size_bytes) + (aItem?.exports_size_bytes ?? 0)
		return bTotal - aTotal
	})
)
const topTimelapses = computed(() => sortedTimelapses.value.slice(0, 5))
const hasMoreTimelapses = computed(() => props.timelapses.length > 5)
const displayedTimelapses = computed(() =>
	showAllTimelapses.value ? sortedTimelapses.value : topTimelapses.value
)

const totalFramesBytes = computed(() =>
	storageStats.value?.timelapse_breakdown.reduce((sum, item) => sum + item.frames_size_bytes, 0) ?? 0
)
const totalExportsBytes = computed(() =>
	storageStats.value?.timelapse_breakdown.reduce((sum, item) => sum + item.exports_size_bytes, 0) ?? 0
)
const systemBytes = computed(() => {
	if (!storageStats.value) return 0
	return Math.max(0, storageStats.value.used_bytes - totalFramesBytes.value - totalExportsBytes.value)
})

function pct(bytes: number): string {
	if (!storageStats.value || storageStats.value.total_bytes === 0) return '0%'
	return `${(bytes / storageStats.value.total_bytes * 100).toFixed(2)}%`
}

onMounted(async () => {
	try {
		storageStats.value = await getStorageStats()
	} catch (err) {
		emit('error', `Failed to fetch storage stats. (${err})`)
	}
})
</script>

<template>
	<Collapsible v-model:open="storageOpen">
		<div class="flex items-center text-muted-foreground mt-6">
			<PhHardDrive size="32" weight="duotone" />
			<h1 class="text-2xl font-bold tracking-wide ml-2">Storage</h1>
			<PhSpinner v-if="loading" :size="24" class="ml-3 text-zinc-700 dark:text-zinc-300 animate-spin" />
			<hr class="border-zinc-300 dark:border-zinc-700 w-full ml-4" />
			<CollapsibleTrigger as-child>
				<button type="button" class="ml-2 p-1 text-zinc-500 hover:text-zinc-300 transition-colors">
					<PhCaretDown :size="20" weight="bold" class="transition-transform duration-200" :class="{ 'rotate-180': storageOpen }" />
				</button>
			</CollapsibleTrigger>
		</div>

		<div v-if="storageStats" class="my-4 px-2">
			<div class="flex justify-between text-sm text-muted-foreground mb-1">
				<span>{{ formatBytes(storageStats.used_bytes) }} used</span>
				<span>{{ formatBytes(storageStats.free_bytes) }} free of {{ formatBytes(storageStats.total_bytes) }}</span>
			</div>
			<div class="w-full h-5 rounded-sm bg-zinc-200 dark:bg-zinc-800 overflow-hidden flex">
				<div class="h-full bg-zinc-300 dark:bg-zinc-600 transition-all" :style="{ width: pct(systemBytes) }" />
				<div class="h-full bg-emerald-500 dark:bg-amber-500 transition-all" :style="{ width: pct(totalFramesBytes) }" />
				<div class="h-full bg-cyan-500 dark:bg-blue-500 transition-all" :style="{ width: pct(totalExportsBytes) }" />
			</div>
			<div class="flex gap-4 mt-1.5 text-xs text-muted-foreground">
				<span class="flex items-center gap-1.5">
					<span class="inline-block w-2.5 h-2.5 rounded-xs bg-zinc-300 dark:bg-zinc-600 shrink-0" />
					System
				</span>
				<span class="flex items-center gap-1.5">
					<span class="inline-block w-2.5 h-2.5 rounded-xs bg-emerald-500 dark:bg-amber-500 shrink-0" />
					Frames
				</span>
				<span v-if="totalExportsBytes > 0" class="flex items-center gap-1.5">
					<span class="inline-block w-2.5 h-2.5 rounded-xs bg-cyan-500 dark:bg-blue-500 shrink-0" />
					Exports
				</span>
			</div>
		</div>

		<CollapsibleContent>
			<div class="p-2">
				<div v-if="timelapses.length > 0">
					<table class="w-full text-sm">
						<thead>
							<tr class="text-left text-muted-foreground border-b border-zinc-200 dark:border-zinc-700">
								<th class="pb-1 font-medium">Timelapse</th>
								<th class="pb-1 font-medium text-right">Frames</th>
								<th class="pb-1 font-medium text-right">Frames size</th>
								<th class="pb-1 font-medium text-right">Exports</th>
							</tr>
						</thead>
						<tbody>
							<tr
								v-for="tl in displayedTimelapses"
								:key="tl.id"
								class="border-b border-zinc-100 dark:border-zinc-800 last:border-0"
							>
								<td class="py-1.5">{{ tl.name }}</td>
								<td class="py-1.5 text-right text-muted-foreground">{{ tl.frame_count.toLocaleString() }}</td>
								<td class="py-1.5 text-right text-muted-foreground">{{ formatBytes(tl.size_bytes) }}</td>
								<td class="py-1.5 text-right text-muted-foreground">
									<span v-if="breakdownMap.has(tl.id) && breakdownMap.get(tl.id)!.exports_size_bytes > 0">
										{{ formatBytes(breakdownMap.get(tl.id)!.exports_size_bytes) }}
									</span>
									<span v-else class="opacity-40">&mdash;</span>
								</td>
							</tr>
						</tbody>
					</table>
					<div v-if="hasMoreTimelapses" class="mt-2 text-center">
						<button
							type="button"
							class="text-xs text-muted-foreground hover:text-foreground transition-colors"
							@click="showAllTimelapses = !showAllTimelapses"
						>
							{{ showAllTimelapses ? 'Show less' : `Show all (${timelapses.length})` }}
						</button>
					</div>
				</div>
				<div v-else class="text-sm text-muted-foreground py-4 text-center">No timelapses yet.</div>
			</div>
		</CollapsibleContent>
	</Collapsible>
</template>
