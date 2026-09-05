<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';

	onMount(() => {
		let isAuthenticated = false;
		const unsub = auth.subscribe((s) => (isAuthenticated = s.isAuthenticated));
		goto(isAuthenticated ? '/qa' : '/login');
		unsub();
	});
</script>

<p>Redirecting...</p>
