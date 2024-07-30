<script lang="ts">
	import { Badge } from 'flowbite-svelte';
	import { eventStore } from '../../../stores/stateStore';

	function getTimeToNextState(time: string | null): string {
		if (time === null || time === undefined || time === '') {
			return '00:00'; // Default value when time is null or undefined
		}
		return time;
	}
</script>

<div class="m-4 flex flex-wrap justify-center text-lg dark:text-white">
	<p class="m-2 text-lg">Event Start</p>
	<Badge border>
		<div>{$eventStore.metadata.eventStart}</div>
	</Badge>

	<p class="m-2 text-lg">Time to Next State</p>
	<Badge border>
		<div>{getTimeToNextState($eventStore.metadata.timeToNextEvent)}</div>
	</Badge>

	<p class="m-2 text-lg">Running Clock</p>
	<Badge border>
		<div>{$eventStore.metadata.runningClock}</div>
	</Badge>
</div>
