<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FrameResponse } from '@/types'
import { getFramesPaginated, deleteFrame } from '@/api/frame'
import {
	AlertDialog, AlertDialogContent,
	AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
	AlertDialogFooter, AlertDialogCancel, AlertDialogAction,
} from '@/components/ui/alert-dialog'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { PhImages, PhTrash, PhWarning, PhCaretDown } from '@phosphor-icons/vue'
import { ScrollAreaRoot, ScrollAreaViewport, ScrollAreaCorner } from 'reka-ui'
import ScrollBar from '../ui/scroll-area/ScrollBar.vue'
import { format } from 'date-fns'

const LIMIT = 24

const props = defineProps<{
	timelapseId: number
	frameCount: number
}>()

const emit = defineEmits<{
	(e: 'error', message: string): void
	(e: 'frame-deleted'): void
}>()

const isOpen = ref(false)
const frames = ref<FrameResponse[]>([])
const total = ref(0)
const isLoading = ref(false)
const frameToDelete = ref<FrameResponse | null>(null)
const imageErrors = ref<Set<number>>(new Set())

const hasMore = computed(() => frames.value.length < total.value)
// Use the prop count in the header before the first load, API total after
const displayTotal = computed(() => total.value > 0 ? total.value : props.frameCount)

// Load only on first open
watch(isOpen, (open) => {
	if (open && frames.value.length === 0 && !isLoading.value) {
		loadInitial()
	}
})

async function loadInitial() {
	isLoading.value = true
	try {
		const result = await getFramesPaginated(props.timelapseId, 0, LIMIT, 'desc')
		frames.value = result.frames
		total.value = result.total
	} catch (err) {
		emit('error', `Failed to load frames. (${err instanceof Error ? err.message : 'Unknown error'})`)
	} finally {
		isLoading.value = false
	}
}

async function loadMore() {
	if (isLoading.value || !hasMore.value) return
	isLoading.value = true
	try {
		const result = await getFramesPaginated(props.timelapseId, frames.value.length, LIMIT, 'desc')
		frames.value.push(...result.frames)
		total.value = result.total
	} catch (err) {
		emit('error', `Failed to load frames. (${err instanceof Error ? err.message : 'Unknown error'})`)
	} finally {
		isLoading.value = false
	}
}

function onScroll(e: Event) {
	const el = e.currentTarget as HTMLElement
	if (isLoading.value || !hasMore.value) return
	if (el.scrollLeft + el.clientWidth >= el.scrollWidth - 300) {
		loadMore()
	}
}

async function doDeleteFrame() {
	if (!frameToDelete.value) return
	const target = frameToDelete.value
	frameToDelete.value = null
	try {
		await deleteFrame(target.id)
		frames.value = frames.value.filter(f => f.id !== target.id)
		total.value = Math.max(0, total.value - 1)
		emit('frame-deleted')
	} catch (err) {
		emit('error', `Failed to delete frame #${target.id}. (${err instanceof Error ? err.message : 'Unknown error'})`)
	}
}
</script>

<template>
	<Collapsible
		v-model:open="isOpen"
		class="border rounded-lg bg-zinc-100 dark:bg-zinc-900 overflow-hidden"
	>
		<!-- Header / trigger -->
		<CollapsibleTrigger class="w-full px-4 pt-3 pb-3 flex items-center gap-2 cursor-pointer hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50 transition-colors text-left outline-none focus-visible:outline-none">
			<PhImages variant="duotone" :size="16" class="text-zinc-400" />
			<h2 class="text-sm font-medium">Frame Explorer</h2>
			<span v-if="isOpen && total > 0" class="text-xs text-muted-foreground">
				(Hold Shift to scroll horizontally)
			</span>
			<div class="ml-auto flex items-center gap-2">
				<span class="text-xs text-muted-foreground">
					<template v-if="isOpen && total > 0">{{ frames.length }} of {{ total }} loaded · newest first</template>
					<template v-else>{{ displayTotal }}</template>
				</span>
				<PhCaretDown
					:size="16"
					class="text-zinc-400 transition-transform duration-200 shrink-0"
					:class="{ 'rotate-180': isOpen }"
				/>
			</div>
		</CollapsibleTrigger>

		<!-- Scrollable frame strip -->
		<CollapsibleContent class=" focus-visible:ring-0">
			<div class="border-t border-zinc-200 dark:border-zinc-700">
				<ScrollAreaRoot class="relative">
					<ScrollAreaViewport
						class="size-full rounded-[inherit] outline-none"
						@scroll.passive="onScroll"
					>
						<div class="flex gap-2 px-3 py-3">
							<!-- Frame cards -->
							<div
								v-for="frame in frames"
								:key="frame.id"
								class="shrink-0 w-48 group"
							>
								<div class="relative aspect-video rounded-md overflow-hidden bg-zinc-200 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700">
									<img
										v-if="!imageErrors.has(frame.id)"
										:src="`/api/v1/frames/${frame.id}/image`"
										loading="lazy"
										class="w-full h-full object-cover"
										@error="imageErrors.add(frame.id)"
									/>
									<div v-else class="absolute inset-0 flex items-center justify-center text-zinc-400">
										<PhWarning weight="duotone" :size="20" />
									</div>

									<!-- Delete button (hover) -->
									<button
										class="absolute top-1 right-1 p-1 rounded bg-black/60 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600/80 cursor-pointer"
										:title="`Delete frame #${frame.id}`"
										@click="frameToDelete = frame"
									>
										<PhTrash weight="duotone" :size="16" />
									</button>
								</div>
								<p class="mt-1 text-xs text-muted-foreground truncate text-center">{{ format(frame.captured_at, "MMM do, h:mm a") }}</p>
							</div>

							<!-- Loading indicator -->
							<div v-if="isLoading" class="shrink-0 w-12 flex items-start pt-3 justify-center">
								<svg class="animate-spin h-4 w-4 text-zinc-400" viewBox="0 0 24 24" fill="none">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
								</svg>
							</div>

							<!-- Beginning-of-timelapse marker -->
							<div
								v-else-if="!hasMore && frames.length > 0"
								class="shrink-0 self-start pt-3 text-[10px] text-muted-foreground whitespace-nowrap px-2"
							>
								Beginning of timelapse
							</div>
						</div>
					</ScrollAreaViewport>
					<ScrollBar orientation="horizontal" />
					<ScrollAreaCorner />
				</ScrollAreaRoot>
			</div>
		</CollapsibleContent>
	</Collapsible>

	<!-- Delete confirmation dialog -->
	<AlertDialog :open="frameToDelete !== null">
		<AlertDialogContent>
			<AlertDialogHeader>
				<AlertDialogTitle>Delete frame?</AlertDialogTitle>
				<AlertDialogDescription>
					Frame #{{ frameToDelete?.id }} captured {{ frameToDelete ? format(frameToDelete.captured_at, "MMM do, h:mm a") : '' }} will be permanently removed from disk.<br>
					<strong>This action cannot be undone.</strong>

					<img
						v-if="frameToDelete"
						:src="`/api/v1/frames/${frameToDelete.id}/image`"
						loading="lazy"
						class="w-fit h-auto object-cover rounded mt-4"
					/>
				</AlertDialogDescription>
			</AlertDialogHeader>
			<AlertDialogFooter>
				<AlertDialogCancel @click="frameToDelete = null">Cancel</AlertDialogCancel>
				<AlertDialogAction
					@click="doDeleteFrame"
					class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
				>
					Delete
				</AlertDialogAction>
			</AlertDialogFooter>
		</AlertDialogContent>
	</AlertDialog>
</template>
