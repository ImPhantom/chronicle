<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { CameraResponse, type TimelapseResponse } from '@/types'
import TimelapseDialog from '@/components/TimelapseDialog.vue';
import { a } from 'vue-router/dist/index-Cu9B0wDz.mjs';
import { PhCamera, PhCameraSlash } from '@phosphor-icons/vue';
import ConnectionTypeBadge from '@/components/ConnectionTypeBadge.vue';

// placeholder — wire to API later
const cameras = ref<CameraResponse[]>([])
const timelapses = ref<TimelapseResponse[]>([])
const fetchData = async () => {
	try {
		const _timelapses = await fetch('/api/v1/timelapses')
		timelapses.value = await _timelapses.json()

		const _cameras = await fetch('/api/v1/cameras')
		cameras.value = await _cameras.json()
	} catch {
		timelapses.value = []
		cameras.value = []
	}
}

onMounted(async () => {
	await fetchData()
})
</script>

<template>
  <div>
	<div class="flex items-center justify-between mb-6">
    	<h1 class="text-2xl font-semibold mb-6">Active Timelapses</h1>
		<TimelapseDialog v-on:timelapse-created="fetchData" />
	</div>

    <div v-if="timelapses.length === 0"
         class="flex flex-col items-center justify-center py-24 text-muted-foreground gap-2">
      	<p class="text-sm">No active timelapses yet.</p>
      	<p class="text-sm">Add a camera from the navbar to get started.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
		<a 
			v-for="timelapse in timelapses"
			:key="timelapse.id"
			class="flex border rounded-lg p-3 gap-3 bg-zinc-900 hover:scale-105 hover:cursor-pointer transition-all"
		>
			<div class="relative aspect-video h-24 rounded-md bg-zinc-800/60 border">
				<!-- last image captured in timelapse -->
				<!-- TODO: implement last frame-->
				<PhCameraSlash variant="duotone" size="32" class="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 text-red-400/40" />
			</div>
			<div class="flex flex-col justify-evenly">
				<h2 class="text-lg font-medium">{{ timelapse.name }}</h2>
				<div class="flex items-center">
					<PhCamera variant="duotone" size="20" class="inline-block mr-1 text-zinc-400" />
					<span class="text-sm ml-1 text-muted-foreground">{{ cameras.find(c => c.id == timelapse.camera_id)?.name || 'Unknown Camera' }}</span>
					<ConnectionTypeBadge :cam="cameras.find(c => c.id == timelapse.camera_id) || { connection_type: 'network' }" />
				</div>
				<p class="text-sm text-muted-foreground">Captures every {{ timelapse.interval_seconds }} seconds</p>
			</div>
			
		</a>
    </div>
  </div>
</template>
