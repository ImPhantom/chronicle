<script setup lang="ts">
import type { Component } from 'vue'
import Button from './ui/button/Button.vue';
import { PhX } from '@phosphor-icons/vue';

type AlertVariant = 'error' | 'success' | 'warning' | 'info'

const props = withDefaults(defineProps<{
	open: boolean
	message?: string
	variant?: AlertVariant
	icon?: Component
	dismissible?: boolean
}>(), {
	variant: 'info',
	dismissible: false
})

/*const emit = defineEmits<{
	(e: 'close'): void
}>()*/

const variantClasses: Record<AlertVariant, {
	container: string
	icon: string
	button: string
}> = {
	error: {
		container: 'border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-300',
		icon: 'text-red-400',
		button: 'border-red-400 text-red-400 hover:bg-red-500/10'
	},
	success: {
		container: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
		icon: 'text-emerald-400',
		button: 'border-emerald-400 text-emerald-400 hover:bg-emerald-500/10'
	},
	warning: {
		container: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
		icon: 'text-amber-400',
		button: 'border-amber-400 text-amber-400 hover:bg-amber-500/10'
	},
	info: {
		container: 'border-indigo-500/30 bg-indigo-500/10 text-indigo-300',
		icon: 'text-indigo-400',
		button: 'border-indigo-400 text-indigo-400 hover:bg-indigo-500/10'
	},
}
</script>

<template>
	<div v-if="open" class="flex items-center gap-3 px-4 py-1.5 min-h-12 rounded-lg border" :class="variantClasses[variant].container">
		<component v-if="icon" :is="icon" variant="duotone" :size="24" class="shrink-0" :class="variantClasses[variant].icon" />

		<span class="text-sm">
			<slot v-if="!message"></slot>
			<span v-else>{{ message }}</span>
		</span>

		<Button v-if="dismissible" size="icon-sm" variant="ghost" class="ml-auto" :class="variantClasses[variant].button" @click="open = false">
			<PhX :size="14" weight="bold" />
		</Button>
	</div>
</template>