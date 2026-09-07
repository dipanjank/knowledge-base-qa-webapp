<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { api } from '$lib/api';
	import { auth } from '$lib/stores/auth';

	let role: string | null = $state(null);
	auth.subscribe((s) => (role = s.role));

	async function handleLogout() {
		try {
			await api('/api/auth/logout', { method: 'POST' });
		} finally {
			auth.logout();
			goto('/login');
		}
	}

	function isActive(path: string): boolean {
		return page.url.pathname.startsWith(path);
	}
</script>

<nav>
	<a href="/qa" class="brand">KB QA</a>
	<div class="links">
		<a href="/documents" class:active={isActive('/documents')}>Documents</a>
		<a href="/rag-jobs" class:active={isActive('/rag-jobs')}>Jobs</a>
		<a href="/qa" class:active={isActive('/qa')}>QA</a>
		{#if role === 'admin'}
			<a href="/admin/users" class:active={isActive('/admin')}>Admin</a>
		{/if}
		<button onclick={handleLogout}>Logout</button>
	</div>
</nav>

<style>
	nav {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1.5rem;
		height: 3.5rem;
		border-bottom: 1px solid var(--color-border);
		background: var(--color-bg);
	}

	.brand {
		font-weight: 700;
		font-size: 1.125rem;
		text-decoration: none;
		color: var(--color-text);
	}

	.links {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.links a {
		text-decoration: none;
		font-size: 0.875rem;
		color: var(--color-muted);
	}

	.links a:hover,
	.links a.active {
		color: var(--color-primary);
	}

	button {
		background: none;
		border: none;
		font-size: 0.875rem;
		color: var(--color-muted);
		cursor: pointer;
		padding: 0;
	}

	button:hover {
		color: #dc2626;
	}
</style>
