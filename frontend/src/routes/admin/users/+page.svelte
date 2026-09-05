<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, ApiError } from '$lib/api';
	import { auth } from '$lib/stores/auth';

	interface User {
		id: string;
		username: string;
		email: string;
		role: string;
		created_at: string;
	}

	let users: User[] = $state([]);
	let newUsername = $state('');
	let newEmail = $state('');
	let createdPassword = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		let role: string | null = null;
		const unsub = auth.subscribe((s) => (role = s.role));
		if (role !== 'admin') {
			goto('/qa');
			unsub();
			return;
		}
		unsub();
		loadUsers();
	});

	async function loadUsers() {
		const data = await api<{ items: User[]; total: number }>('/api/admin/users');
		users = data.items;
	}

	async function createUser(e: Event) {
		e.preventDefault();
		error = '';
		createdPassword = '';
		loading = true;

		try {
			const data = await api<{ password: string }>('/api/admin/users', {
				method: 'POST',
				body: JSON.stringify({ username: newUsername, email: newEmail })
			});
			createdPassword = data.password;
			newUsername = '';
			newEmail = '';
			await loadUsers();
		} catch (err) {
			if (err instanceof ApiError) error = err.detail;
		} finally {
			loading = false;
		}
	}

	async function deleteUser(id: string, username: string) {
		if (!confirm(`Delete user "${username}"?`)) return;
		try {
			await api(`/api/admin/users/${id}`, { method: 'DELETE' });
			await loadUsers();
		} catch (err) {
			if (err instanceof ApiError) alert(err.detail);
		}
	}
</script>

<div class="admin-page">
	<h1>User Management</h1>

	<form class="create-form" onsubmit={createUser}>
		<h2>Create User</h2>

		{#if error}
			<p class="error">{error}</p>
		{/if}

		{#if createdPassword}
			<div class="password-display">
				<strong>Generated password (shown once):</strong>
				<code>{createdPassword}</code>
			</div>
		{/if}

		<div class="form-row">
			<label>
				Username
				<input type="text" bind:value={newUsername} required />
			</label>
			<label>
				Email
				<input type="email" bind:value={newEmail} required />
			</label>
			<button type="submit" disabled={loading}>Create</button>
		</div>
	</form>

	<table>
		<thead>
			<tr>
				<th>Username</th>
				<th>Email</th>
				<th>Role</th>
				<th>Created</th>
				<th></th>
			</tr>
		</thead>
		<tbody>
			{#each users as user}
				<tr>
					<td>{user.username}</td>
					<td>{user.email}</td>
					<td>{user.role}</td>
					<td>{new Date(user.created_at).toLocaleDateString()}</td>
					<td>
						{#if user.role !== 'admin'}
							<button class="delete-btn" onclick={() => deleteUser(user.id, user.username)}>
								Delete
							</button>
						{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.admin-page {
		max-width: 800px;
		margin: 2rem auto;
		padding: 0 1.5rem;
	}

	h1 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
	}

	h2 {
		font-size: 1.125rem;
		margin-bottom: 0.75rem;
	}

	.create-form {
		padding: 1.25rem;
		border: 1px solid var(--color-border);
		border-radius: 8px;
		margin-bottom: 2rem;
	}

	.form-row {
		display: flex;
		gap: 1rem;
		align-items: flex-end;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-muted);
		flex: 1;
	}

	input {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: 6px;
		font-size: 0.875rem;
		color: var(--color-text);
	}

	input:focus {
		outline: 2px solid var(--color-primary);
		outline-offset: -1px;
	}

	button[type='submit'] {
		padding: 0.5rem 1.25rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		cursor: pointer;
		white-space: nowrap;
	}

	button[type='submit']:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	.password-display {
		padding: 0.75rem;
		background: #f0fdf4;
		border: 1px solid #bbf7d0;
		border-radius: 6px;
		margin-bottom: 0.75rem;
		font-size: 0.875rem;
	}

	.password-display code {
		display: block;
		margin-top: 0.25rem;
		font-size: 1rem;
		color: var(--color-text);
		user-select: all;
	}

	.error {
		color: #dc2626;
		font-size: 0.875rem;
		padding: 0.5rem;
		background: #fef2f2;
		border-radius: 6px;
		margin-bottom: 0.75rem;
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}

	th,
	td {
		padding: 0.625rem 0.75rem;
		text-align: left;
		border-bottom: 1px solid var(--color-border);
		font-size: 0.875rem;
	}

	th {
		font-weight: 600;
		color: var(--color-muted);
	}

	.delete-btn {
		background: none;
		border: none;
		color: #dc2626;
		font-size: 0.8125rem;
		cursor: pointer;
		padding: 0;
	}

	.delete-btn:hover {
		text-decoration: underline;
	}
</style>
