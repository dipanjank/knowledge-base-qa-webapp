<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleLogin(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;

		try {
			const res = await fetch('/api/auth/login', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({ username, password })
			});

			if (!res.ok) {
				const data = await res.json().catch(() => ({ detail: 'Login failed' }));
				error = data.detail ?? 'Login failed';
				return;
			}

			const data = await res.json();
			auth.setToken(data.access_token, data.expires_in);
			goto('/qa');
		} finally {
			loading = false;
		}
	}
</script>

<div class="login-page">
	<form class="login-form" onsubmit={handleLogin}>
		<h1>Knowledge Base QA</h1>

		{#if error}
			<p class="error">{error}</p>
		{/if}

		<label>
			Username
			<input type="text" bind:value={username} required autocomplete="username" />
		</label>

		<label>
			Password
			<input type="password" bind:value={password} required autocomplete="current-password" />
		</label>

		<button type="submit" disabled={loading}>
			{loading ? 'Signing in...' : 'Sign in'}
		</button>
	</form>
</div>

<style>
	.login-page {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
	}

	.login-form {
		width: 100%;
		max-width: 360px;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	h1 {
		font-size: 1.5rem;
		text-align: center;
		margin-bottom: 0.5rem;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-muted);
	}

	input {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: 6px;
		font-size: 1rem;
		color: var(--color-text);
	}

	input:focus {
		outline: 2px solid var(--color-primary);
		outline-offset: -1px;
	}

	button {
		padding: 0.625rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		margin-top: 0.5rem;
	}

	button:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.error {
		color: #dc2626;
		font-size: 0.875rem;
		text-align: center;
		padding: 0.5rem;
		background: #fef2f2;
		border-radius: 6px;
	}
</style>
