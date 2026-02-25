<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { PhCaretDown, PhHardDrive, PhSpinner } from '@phosphor-icons/vue'
import type { StorageStats, TimelapseResponse } from '@/types'
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
const storageOpen = ref(true)

const showAllTimelapses = ref(false)
const sortedTimelapses = computed(() =>
	[...props.timelapses].sort((a, b) => b.size_bytes - a.size_bytes)
)
const topTimelapses = computed(() => sortedTimelapses.value.slice(0, 5))
const hasMoreTimelapses = computed(() => props.timelapses.length > 5)
const displayedTimelapses = computed(() =>
	showAllTimelapses.value ? sortedTimelapses.value : topTimelapses.value
)

const usedPercent = computed(() => {
	if (!storageStats.value || storageStats.value.total_bytes === 0) return 0
	return (storageStats.value.used_bytes / storageStats.value.total_bytes) * 100
})

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
			<div class="w-full h-3 rounded-xs bg-zinc-200 dark:bg-zinc-700 overflow-hidden">
				<div
					class="h-full rounded-xs bg-linear-to-r from-emerald-500 dark:from-amber-500 to-cyan-700 dark:to-red-800 transition-all"
					:style="{ width: `${usedPercent.toFixed(1)}%` }"
				/>
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
								<th class="pb-1 font-medium text-right">Size</th>
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