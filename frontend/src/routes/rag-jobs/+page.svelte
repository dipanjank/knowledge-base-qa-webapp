<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	interface RagJobDocumentStatus {
		id: string;
		filename: string;
		status: string;
		error_message: string | null;
	}

	interface RagJobResponse {
		id: string;
		status: string;
		total_documents: number;
		documents_processed: number;
		documents_failed: number;
		documents: RagJobDocumentStatus[];
		created_at: string;
		completed_at: string | null;
	}

	let jobs: RagJobResponse[] = $state([]);

	onMount(async () => {
		const data = await api<{ items: RagJobResponse[]; total: number }>('/api/rag-jobs/');
		jobs = data.items;
	});

	function statusBadgeClass(status: string): string {
		switch (status) {
			case 'success':
				return 'badge-success';
			case 'failure':
				return 'badge-error';
			case 'processing':
				return 'badge-processing';
			case 'partial_success':
				return 'badge-warning';
			default:
				return 'badge-pending';
		}
	}

	function formatDuration(created: string, completed: string | null): string {
		if (!completed) return '-';
		const ms = new Date(completed).getTime() - new Date(created).getTime();
		const seconds = Math.floor(ms / 1000);
		if (seconds < 60) return `${seconds}s`;
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = seconds % 60;
		return `${minutes}m ${remainingSeconds}s`;
	}
</script>

<div class="jobs-page">
	<h1>RAG Jobs</h1>

	{#if jobs.length > 0}
		<table>
			<thead>
				<tr>
					<th>Status</th>
					<th>Documents</th>
					<th>Progress</th>
					<th>Created</th>
					<th>Duration</th>
				</tr>
			</thead>
			<tbody>
				{#each jobs as job}
					<tr>
						<td><span class="badge {statusBadgeClass(job.status)}">{job.status}</span></td>
						<td>
							{#each job.documents as doc}
								<div class="doc-row">
									<span>{doc.filename}</span>
									<span class="badge {statusBadgeClass(doc.status)}">{doc.status}</span>
								</div>
							{/each}
						</td>
						<td>{job.documents_processed} / {job.total_documents}</td>
						<td>{new Date(job.created_at).toLocaleString()}</td>
						<td>{formatDuration(job.created_at, job.completed_at)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else}
		<p class="empty">No RAG jobs yet.</p>
	{/if}
</div>

<style>
	.jobs-page {
		max-width: 900px;
		margin: 2rem auto;
		padding: 0 1.5rem;
	}

	h1 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
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
		vertical-align: top;
	}

	th {
		font-weight: 600;
		color: var(--color-muted);
	}

	.doc-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.125rem 0;
		font-size: 0.8125rem;
	}

	.badge {
		display: inline-block;
		padding: 0.125rem 0.5rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
	}

	.badge-success {
		background: #dcfce7;
		color: #166534;
	}

	.badge-error {
		background: #fef2f2;
		color: #991b1b;
	}

	.badge-processing {
		background: #dbeafe;
		color: #1e40af;
	}

	.badge-warning {
		background: #fef3c7;
		color: #92400e;
	}

	.badge-pending {
		background: #f3f4f6;
		color: #6b7280;
	}

	.empty {
		color: var(--color-muted);
		text-align: center;
		padding: 2rem 0;
	}
</style>
