<script setup lang="ts">
import { ref } from 'vue'

const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleTheme() {
	isDark.value = !isDark.value
	document.documentElement.classList.toggle('dark', isDark.value)
	localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}
</script>

<template>
	<header class="border-b bg-background">
		<div class="container mx-auto px-4 h-14 flex items-center justify-between">
			<a href="/" class="font-semibold text-lg tracking-tight">Chronicle</a>
			<div class="flex items-center gap-2">
				<a href="/settings" class="text-sm font-medium">Settings</a>
				<button @click="toggleTheme" class="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors" :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'">
					<!-- Sun icon (shown in dark mode) -->
					<svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="4" />
						<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
					</svg>
					<!-- Moon icon (shown in light mode) -->
					<svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
					</svg>
				</button>
			</div>
		</div>
	</header>
</template>
