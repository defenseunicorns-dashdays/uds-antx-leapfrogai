<script lang="ts">
	import { Button } from 'flowbite-svelte';
	import { Api } from '$lib/api';
	import { updateEventStore } from '../../stores/stateStore';

	async function fetchUpdate() {
		const newData = await Api.update();
		updateEventStore(newData);
	}
</script>

<div class="flex justify-center">
	<Button class="m-2 mt-8 border dark:bg-gray-700" color="primary" size="lg" on:click={Api.start}
		>Start</Button
	>
	<Button class="m-2 mt-8 border dark:bg-gray-700" color="primary" size="lg" on:click={fetchUpdate}
		>Update</Button
	>
	<Button class="m-2 mt-8 border dark:bg-gray-700" color="primary" size="lg" on:click={Api.end}
		>End</Button
	>
</div>
