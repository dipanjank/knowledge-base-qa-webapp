<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import Navbar from '$lib/components/Navbar.svelte';

	let { children } = $props();

	let isAuthenticated = $state(false);
	auth.subscribe((s) => (isAuthenticated = s.isAuthenticated));

	const publicPaths = ['/login'];

	$effect(() => {
		const path = page.url.pathname;
		if (!isAuthenticated && !publicPaths.includes(path)) {
			goto('/login');
		}
	});
</script>

{#if isAuthenticated && !publicPaths.includes(page.url.pathname)}
	<Navbar />
{/if}

{@render children()}
