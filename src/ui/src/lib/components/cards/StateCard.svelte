<script lang="ts">
	import { Card } from 'flowbite-svelte';
	import { eventStore } from '../../../stores/stateStore';

	const mainStates = [
		'Pre Trial Start',
		'Trial Start',
		'Trial End',
		'In Transit',
		'Mistrial',
		'RTB'
	];

	const delayStates = ['Delay Start', 'Delay End'];
</script>

<div class="m-4 flex flex-col items-center dark:text-white">
	<div class="flex flex-wrap justify-center">
		{#each mainStates as state}
			<div
				class="m-2 min-w-[200px] text-center {$eventStore.state.currentState === state
					? 'glow-border'
					: 'glow-border-inactive'} rounded-lg border-transparent"
			>
				<Card color="primary" class="dark:bg-gray-700">{state}</Card>
			</div>
		{/each}
	</div>

	<div class="mt-4 flex flex-wrap justify-center">
		{#each delayStates as state}
			<div
				class="m-2 min-w-[200px] text-center {$eventStore.state.currentState === state
					? 'glow-border'
					: 'glow-border-inactive'} rounded-lg border-transparent"
			>
				<Card color="primary" class="dark:bg-gray-700">{state}</Card>
			</div>
		{/each}
	</div>
</div>

<style>
	@keyframes glow {
		0% {
			box-shadow:
				0 0 5px #2494d1,
				0 0 10px #2494d1,
				0 0 15px #2494d1,
				0 0 20px #2494d1;
		}
		50% {
			box-shadow:
				0 0 10px #2494d1,
				0 0 20px #2494d1,
				0 0 30px #2494d1,
				0 0 40px #2494d1;
		}
		100% {
			box-shadow:
				0 0 5px #2494d1,
				0 0 10px #2494d1,
				0 0 15px #2494d1,
				0 0 20px #2494d1;
		}
	}

	.glow-border {
		animation: glow 2s infinite;
	}

	.glow-border-inactive {
		animation: none;
	}
</style>
