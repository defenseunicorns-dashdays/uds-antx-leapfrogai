<script lang="ts">
	import ClocksCard from '$lib/components/cards/ClocksCard.svelte';
	import StateCard from '$lib/components/cards/StateCard.svelte';
	import Transcript from '$lib/components/cards/Transcript.svelte';
	import PerformanceCard from '$lib/components/cards/PerformanceCard.svelte';
	import { Accordion, AccordionItem, Button } from 'flowbite-svelte';
	import { Api } from '$lib/api';
	import { updateEventStore } from '../stores/stateStore';

	const delayStates = [
		{ state: 'Delay Start', isCurrent: false },
		{ state: 'Delay End', isCurrent: false }
	];

	const dummyTranscript = [
		'Alpha: Tango 1, this is Bravo Actual, over.',
		'Tango 1: Bravo Actual, this is Tango 1, go ahead, over.',
		'Bravo Actual: Tango 1, be advised, enemy forces spotted at grid coordinates 123456, over.',
		'Tango 1: Copy that, Bravo Actual. We will proceed with caution, over.',
		'Alpha: Tango 1, this is Bravo Actual, over.',
		'Tango 1: Bravo Actual, this is Tango 1, go ahead, over.',
		'Bravo Actual: Tango 1, be advised, enemy forces spotted at grid coordinates 123456, over.',
		'Tango 1: Copy that, Bravo Actual. We will proceed with caution, over.',
		'Alpha: Tango 1, this is Bravo Actual, over.',
		'Tango 1: Bravo Actual, this is Tango 1, go ahead, over.',
		'Bravo Actual: Tango 1, be advised, enemy forces spotted at grid coordinates 123456, over.',
		'Tango 1: Copy that, Bravo Actual. We will proceed with caution, over.',
		'Alpha: Tango 1, this is Bravo Actual, over.',
		'Tango 1: Bravo Actual, this is Tango 1, go ahead, over.',
		'Bravo Actual: Tango 1, be advised, enemy forces spotted at grid coordinates 123456, over.',
		'Tango 1: Copy that, Bravo Actual. We will proceed with caution, over.',
		'short line'
	];

	async function fetchUpdate() {
		const newData = await Api.update();
		updateEventStore(newData);
	}

	function startUpdateInterval() {
		setInterval(fetchUpdate, 3000);
	}

	startUpdateInterval();
</script>

<ClocksCard />
<StateCard />
<!-- <StateCard list={delayStates} /> -->

<Accordion multiple class="mx-auto w-5/6">
	<AccordionItem open>
		<span slot="header">Transcript</span>
		<Transcript list={dummyTranscript} />
	</AccordionItem>
	<AccordionItem open>
		<span slot="header">Performance Metrics</span>
		<PerformanceCard />
	</AccordionItem>
</Accordion>
