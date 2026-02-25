<script setup lang="ts">
import { PhArrowLeft } from '@phosphor-icons/vue';
</script>

<template>
	<div class="flex items-center justify-center px-4">
		<div class="w-full max-w-2xl mt-16 text-center">
			<div class="mb-8">
				<h1 class="text-[8rem] font-black leading-none bg-linear-to-r from-emerald-500 dark:from-amber-500 to-cyan-700 dark:to-red-800 bg-clip-text text-transparent select-none">
					404
				</h1>
			</div>

			<h2 class="mb-3 text-3xl font-bold">Page Not Found</h2>
			<p class="mb-6 text-lg text-muted-foreground">The page you're looking for doesn't exist.</p>

			<RouterLink to="/" class="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
				<PhArrowLeft variant="duotone" :size="16" />
				Back to Dashboard
			</RouterLink>
		</div>
	</div>
</template>