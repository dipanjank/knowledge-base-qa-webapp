<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { api, ApiError } from '$lib/api';

	interface DocumentInfo {
		id: string;
		filename: string;
	}

	interface DocumentResponse {
		id: string;
		filename: string;
		file_type: string;
		file_size_bytes: number;
		status: string;
		text_preview: string | null;
		created_at: string;
		indexed_at: string | null;
	}

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

	let documents: DocumentResponse[] = $state([]);
	let activeJob: RagJobResponse | null = $state(null);
	let files: FileList | null = $state(null);
	let uploading = $state(false);
	let error = $state('');
	let pollInterval: ReturnType<typeof setInterval> | null = null;

	onMount(() => {
		loadDocuments();
		checkActiveJob();
	});

	onDestroy(() => {
		stopPolling();
	});

	async function loadDocuments() {
		const data = await api<{ items: DocumentResponse[]; total: number }>('/api/documents/');
		documents = data.items;
	}

	async function checkActiveJob() {
		const job = await api<RagJobResponse | null>('/api/rag-jobs/active');
		activeJob = job;
		if (job && (job.status === 'pending' || job.status === 'processing')) {
			startPolling();
		}
	}

	function startPolling() {
		if (pollInterval) return;
		pollInterval = setInterval(async () => {
			const job = await api<RagJobResponse | null>('/api/rag-jobs/active');
			activeJob = job;
			if (!job || (job.status !== 'pending' && job.status !== 'processing')) {
				stopPolling();
				await loadDocuments();
			}
		}, 3000);
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
	}

	async function handleUpload(e: Event) {
		e.preventDefault();
		if (!files || files.length === 0) return;

		error = '';
		uploading = true;

		try {
			const formData = new FormData();
			for (const file of files) {
				formData.append('files', file);
			}

			const data = await api<{ job_id: string; documents: DocumentInfo[] }>('/api/documents/', {
				method: 'POST',
				body: formData
			});

			files = null;
			const input = document.querySelector<HTMLInputElement>('input[type="file"]');
			if (input) input.value = '';

			activeJob = {
				id: data.job_id,
				status: 'pending',
				total_documents: data.documents.length,
				documents_processed: 0,
				documents_failed: 0,
				documents: data.documents.map((d) => ({
					id: d.id,
					filename: d.filename,
					status: 'pending',
					error_message: null
				})),
				created_at: new Date().toISOString(),
				completed_at: null
			};
			startPolling();
			await loadDocuments();
		} catch (err) {
			if (err instanceof ApiError) error = err.detail;
		} finally {
			uploading = false;
		}
	}

	async function deleteDocument(id: string, filename: string) {
		if (!confirm(`Delete "${filename}"?`)) return;
		try {
			await api(`/api/documents/${id}`, { method: 'DELETE' });
			await loadDocuments();
		} catch (err) {
			if (err instanceof ApiError) alert(err.detail);
		}
	}

	function statusBadgeClass(status: string): string {
		switch (status) {
			case 'ready':
			case 'success':
				return 'badge-success';
			case 'failed':
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

	function formatBytes(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function isJobActive(job: RagJobResponse | null): boolean {
		return job !== null && (job.status === 'pending' || job.status === 'processing');
	}

	let hasActiveJob = $derived(isJobActive(activeJob));
</script>

<div class="documents-page">
	<h1>Documents</h1>

	<!-- Upload Form -->
	<form class="upload-form" onsubmit={handleUpload}>
		<h2>Upload Documents</h2>

		{#if error}
			<p class="error">{error}</p>
		{/if}

		<div class="upload-row">
			<input type="file" accept=".txt" multiple bind:files disabled={!!hasActiveJob || uploading} />
			<button type="submit" disabled={!!hasActiveJob || uploading || !files || files.length === 0}>
				{uploading ? 'Uploading...' : 'Upload'}
			</button>
		</div>
		<p class="hint">Up to 5 .txt files per upload</p>
		{#if hasActiveJob}
			<p class="hint processing-hint">Upload disabled while a job is processing.</p>
		{/if}
	</form>

	<!-- Active Job Status Panel -->
	{#if activeJob}
		<div class="job-panel">
			<div class="job-header">
				<h2>Processing Job</h2>
				<span class="badge {statusBadgeClass(activeJob.status)}">{activeJob.status}</span>
			</div>
			<div class="progress-bar-container">
				<div
					class="progress-bar"
					style="width: {activeJob.total_documents > 0
						? (activeJob.documents_processed / activeJob.total_documents) * 100
						: 0}%"
				></div>
			</div>
			<p class="progress-text">
				{activeJob.documents_processed} / {activeJob.total_documents} documents processed
				{#if activeJob.documents_failed > 0}
					({activeJob.documents_failed} failed)
				{/if}
			</p>
			<ul class="job-doc-list">
				{#each activeJob.documents as doc}
					<li>
						<span class="doc-name">{doc.filename}</span>
						<span class="badge {statusBadgeClass(doc.status)}">{doc.status}</span>
						{#if doc.error_message}
							<span class="doc-error">{doc.error_message}</span>
						{/if}
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	<!-- Document List -->
	{#if documents.length > 0}
		<table>
			<thead>
				<tr>
					<th>Filename</th>
					<th>Size</th>
					<th>Status</th>
					<th>Uploaded</th>
					<th></th>
				</tr>
			</thead>
			<tbody>
				{#each documents as doc}
					<tr>
						<td>{doc.filename}</td>
						<td>{formatBytes(doc.file_size_bytes)}</td>
						<td><span class="badge {statusBadgeClass(doc.status)}">{doc.status}</span></td>
						<td>{new Date(doc.created_at).toLocaleDateString()}</td>
						<td>
							<button class="delete-btn" onclick={() => deleteDocument(doc.id, doc.filename)}>
								Delete
							</button>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else}
		<p class="empty">No documents uploaded yet.</p>
	{/if}
</div>

<style>
	.documents-page {
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

	.upload-form {
		padding: 1.25rem;
		border: 1px solid var(--color-border);
		border-radius: 8px;
		margin-bottom: 1.5rem;
	}

	.upload-row {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	input[type='file'] {
		font-size: 0.875rem;
		color: var(--color-text);
		flex: 1;
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

	button[type='submit']:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.hint {
		font-size: 0.8125rem;
		color: var(--color-muted);
		margin-top: 0.5rem;
	}

	.processing-hint {
		color: #d97706;
	}

	.error {
		color: #dc2626;
		font-size: 0.875rem;
		padding: 0.5rem;
		background: #fef2f2;
		border-radius: 6px;
		margin-bottom: 0.75rem;
	}

	/* Job Status Panel */
	.job-panel {
		padding: 1.25rem;
		border: 1px solid var(--color-border);
		border-radius: 8px;
		margin-bottom: 1.5rem;
		background: var(--color-bg);
	}

	.job-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.job-header h2 {
		margin-bottom: 0;
	}

	.progress-bar-container {
		height: 6px;
		background: var(--color-border);
		border-radius: 3px;
		margin: 0.75rem 0 0.5rem;
		overflow: hidden;
	}

	.progress-bar {
		height: 100%;
		background: var(--color-primary);
		border-radius: 3px;
		transition: width 0.3s ease;
	}

	.progress-text {
		font-size: 0.8125rem;
		color: var(--color-muted);
		margin-bottom: 0.75rem;
	}

	.job-doc-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.job-doc-list li {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.375rem 0;
		font-size: 0.875rem;
		border-bottom: 1px solid var(--color-border);
	}

	.job-doc-list li:last-child {
		border-bottom: none;
	}

	.doc-name {
		flex: 1;
	}

	.doc-error {
		font-size: 0.75rem;
		color: #dc2626;
	}

	/* Badges */
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

	/* Document Table */
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

	.empty {
		color: var(--color-muted);
		text-align: center;
		padding: 2rem 0;
	}
</style>
