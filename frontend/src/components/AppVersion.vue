<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { PhArrowUp } from '@phosphor-icons/vue'
import { getVersion } from '@/api/version'

const gitHash = ref('')
const gitHashFull = ref('')
const updateAvailable = ref(false)

onMounted(async () => {
	try {
		const info = await getVersion()
		gitHash.value = info.git_hash
		gitHashFull.value = info.git_hash_full
	} catch {
		return
	}

	if (gitHashFull.value === 'unknown') return

	try {
		const res = await fetch('https://api.github.com/repos/ImPhantom/chronicle/commits/master')
		if (res.ok) {
			const data = await res.json()
			if (data.sha && data.sha !== gitHashFull.value) {
				updateAvailable.value = true
			}
		}
	} catch {
		// update check is non-critical; silently ignore errors
	}
})
</script>

<template>
	<div
		v-if="gitHash"
		class="flex items-center gap-1.5 text-[12px] text-muted-foreground/70"
	>
		<span>{{ gitHash }}</span>
		<a
			v-if="updateAvailable"
			:href="`https://github.com/ImPhantom/chronicle/commit/${gitHashFull}`"
			target="_blank"
			rel="noopener noreferrer"
			class="flex items-center gap-0.5 text-amber-500/70 hover:text-amber-500 transition-colors"
			title="Update available"
		>
			<PhArrowUp :size="10" weight="bold" />
			update available
		</a>
	</div>
</template>
