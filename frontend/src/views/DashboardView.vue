<script setup lang="ts">
import TimelapseDialog from '@/components/TimelapseDialog.vue';

// placeholder — wire to API later
const timelapses: [] = []
</script>

<template>
  <div>
	<div class="flex items-center justify-between mb-6">
    	<h1 class="text-2xl font-semibold mb-6">Active Timelapses</h1>
		<TimelapseDialog />
	</div>

    <div v-if="timelapses.length === 0"
         class="flex flex-col items-center justify-center py-24 text-muted-foreground gap-2">
      <p class="text-sm">No active timelapses yet.</p>
      <p class="text-sm">Add a camera from the navbar to get started.</p>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- timelapse cards go here -->
    </div>
  </div>
</template>
