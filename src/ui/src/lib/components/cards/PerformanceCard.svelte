<script lang="ts">
	import { Badge } from 'flowbite-svelte';
	import { eventStore } from '../../../stores/stateStore';

	function formatNumber(num: number): string {
		return num.toFixed(1);
	}
</script>

<div class="m-4 flex grid grid-cols-2 flex-wrap justify-center text-xl">
	<div class="grid grid-cols-1">
		<p>Transcription Time (s)</p>
		<div class="grid grid-cols-2 p-4 indent-10">
			<span>minimum</span>
			<Badge class="m-0.5 w-1/2" border>{formatNumber($eventStore.performanceMetrics.timeToTranscribePerToken.min)}</Badge>
			<span>maximum</span>
			<Badge class="m-0.5 w-1/2" border>{formatNumber($eventStore.performanceMetrics.timeToTranscribePerToken.max)}</Badge>
			<span>average</span>
			<Badge class="m-0.5 w-1/2" border>{formatNumber($eventStore.performanceMetrics.timeToTranscribePerToken.avg)}</Badge>
		</div>
	</div>
	<div class="grid grid-cols-1">
		<p>Inferencing Time (s)</p>
		<div class="grid grid-cols-2 p-4 indent-10">
			<span>minimum</span>
			<Badge class="m-0.5 w-1/2" border>{formatNumber($eventStore.performanceMetrics.timeToInference.min)}</Badge>
			<span>maximum</span>
			<Badge class="m-0.5 w-1/2" border>{formatNumber($eventStore.performanceMetrics.timeToInference.max)}</Badge>
			<span>average</span>
			<Badge class="m-0.5 w-1/2" border>{formatNumber($eventStore.performanceMetrics.timeToInference.avg)}</Badge>
		</div>
	</div>
</div>