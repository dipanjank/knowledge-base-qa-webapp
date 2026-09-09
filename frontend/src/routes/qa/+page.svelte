<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { api, ApiError } from '$lib/api';

	interface SourceInfo {
		document_id: string;
		filename: string;
		excerpt: string;
	}

	interface MessageResponse {
		id: string;
		role: string;
		content: string;
		sources: SourceInfo[] | null;
		created_at: string;
	}

	interface ConversationSummary {
		id: string;
		title: string;
		created_at: string;
		updated_at: string;
	}

	interface ConversationListResponse {
		items: ConversationSummary[];
		total: number;
	}

	interface ConversationDetailResponse {
		id: string;
		title: string;
		messages: MessageResponse[];
	}

	interface AskResponse {
		answer: string;
		sources: SourceInfo[];
		conversation_id: string;
	}

	let conversations: ConversationSummary[] = $state([]);
	let activeConversationId: string | null = $state(null);
	let messages: MessageResponse[] = $state([]);
	let question = $state('');
	let asking = $state(false);
	let error = $state('');
	let messagesEl: HTMLDivElement | undefined = $state(undefined);

	onMount(() => {
		loadConversations();
	});

	async function loadConversations() {
		try {
			const data = await api<ConversationListResponse>('/api/qa/conversations');
			conversations = data.items;
		} catch (err) {
			if (err instanceof ApiError) error = err.detail;
		}
	}

	async function selectConversation(id: string) {
		error = '';
		try {
			const data = await api<ConversationDetailResponse>(`/api/qa/conversations/${id}`);
			activeConversationId = id;
			messages = data.messages;
			await scrollToBottom();
		} catch (err) {
			if (err instanceof ApiError) error = err.detail;
		}
	}

	function startNewConversation() {
		activeConversationId = null;
		messages = [];
		error = '';
	}

	async function handleAsk(e: Event) {
		e.preventDefault();
		const q = question.trim();
		if (!q || asking) return;

		error = '';
		asking = true;

		messages = [
			...messages,
			{
				id: Math.random().toString(36).slice(2),
				role: 'human',
				content: q,
				sources: null,
				created_at: new Date().toISOString()
			}
		];
		question = '';
		await scrollToBottom();

		try {
			const data = await api<AskResponse>('/api/qa/ask', {
				method: 'POST',
				body: JSON.stringify({
					question: q,
					conversation_id: activeConversationId
				})
			});

			activeConversationId = data.conversation_id;

			messages = [
				...messages,
				{
					id: Math.random().toString(36).slice(2),
					role: 'ai',
					content: data.answer,
					sources: data.sources.length > 0 ? data.sources : null,
					created_at: new Date().toISOString()
				}
			];
			await scrollToBottom();
			await loadConversations();
		} catch (err) {
			if (err instanceof ApiError) error = err.detail;
			else error = 'Something went wrong';
		} finally {
			asking = false;
		}
	}

	async function scrollToBottom() {
		await tick();
		if (messagesEl) {
			messagesEl.scrollTop = messagesEl.scrollHeight;
		}
	}

	function formatTime(iso: string): string {
		return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString();
	}
</script>

<div class="qa-page">
	<aside class="sidebar">
		<div class="sidebar-header">
			<h2>Conversations</h2>
			<button class="new-btn" onclick={startNewConversation}>New</button>
		</div>
		<ul class="conversation-list">
			{#each conversations as conv}
				<li>
					<button
						class="conversation-item"
						class:active={conv.id === activeConversationId}
						onclick={() => selectConversation(conv.id)}
					>
						<span class="conv-title">{conv.title}</span>
						<span class="conv-date">{formatDate(conv.updated_at)}</span>
					</button>
				</li>
			{/each}
			{#if conversations.length === 0}
				<li class="empty-hint">No conversations yet</li>
			{/if}
		</ul>
	</aside>

	<main class="chat-area">
		{#if error}
			<p class="error">{error}</p>
		{/if}

		<div class="messages" bind:this={messagesEl}>
			{#if messages.length === 0 && !asking}
				<div class="welcome">
					<h1>Question Answering</h1>
					<p>Ask questions about your uploaded documents.</p>
				</div>
			{/if}

			{#each messages as msg}
				<div class="message {msg.role}">
					<div class="message-label">{msg.role === 'human' ? 'You' : 'Assistant'}</div>
					<div class="message-content">{msg.content}</div>
					{#if msg.sources && msg.sources.length > 0}
						<details class="sources">
							<summary>{msg.sources.length} source{msg.sources.length > 1 ? 's' : ''}</summary>
							<ul>
								{#each msg.sources as src}
									<li>
										<strong>{src.filename}</strong>
										<p class="excerpt">{src.excerpt}</p>
									</li>
								{/each}
							</ul>
						</details>
					{/if}
				</div>
			{/each}

			{#if asking}
				<div class="message ai">
					<div class="message-label">Assistant</div>
					<div class="message-content thinking">Thinking...</div>
				</div>
			{/if}
		</div>

		<form class="input-area" onsubmit={handleAsk}>
			<input
				type="text"
				placeholder="Ask a question about your documents..."
				bind:value={question}
				disabled={asking}
			/>
			<button type="submit" disabled={asking || !question.trim()}>
				{asking ? 'Asking...' : 'Ask'}
			</button>
		</form>
	</main>
</div>

<style>
	.qa-page {
		display: flex;
		height: calc(100vh - 56px);
		overflow: hidden;
	}

	/* Sidebar */
	.sidebar {
		width: 260px;
		border-right: 1px solid var(--color-border);
		display: flex;
		flex-direction: column;
		flex-shrink: 0;
	}

	.sidebar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem;
		border-bottom: 1px solid var(--color-border);
	}

	.sidebar-header h2 {
		font-size: 1rem;
		font-weight: 600;
	}

	.new-btn {
		padding: 0.25rem 0.75rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 0.8125rem;
		cursor: pointer;
	}

	.new-btn:hover {
		background: var(--color-primary-hover);
	}

	.conversation-list {
		list-style: none;
		overflow-y: auto;
		flex: 1;
	}

	.conversation-item {
		display: block;
		width: 100%;
		padding: 0.75rem 1rem;
		text-align: left;
		background: none;
		border: none;
		border-bottom: 1px solid var(--color-border);
		cursor: pointer;
		font-size: 0.8125rem;
	}

	.conversation-item:hover {
		background: #f9fafb;
	}

	.conversation-item.active {
		background: #eff6ff;
		border-left: 3px solid var(--color-primary);
	}

	.conv-title {
		display: block;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		color: var(--color-text);
	}

	.conv-date {
		display: block;
		font-size: 0.75rem;
		color: var(--color-muted);
		margin-top: 0.125rem;
	}

	.empty-hint {
		padding: 1rem;
		color: var(--color-muted);
		font-size: 0.8125rem;
		text-align: center;
	}

	/* Chat Area */
	.chat-area {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.error {
		color: #dc2626;
		font-size: 0.875rem;
		padding: 0.5rem 1rem;
		background: #fef2f2;
		margin: 0.5rem 1rem;
		border-radius: 6px;
	}

	.messages {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem;
	}

	.welcome {
		text-align: center;
		padding: 4rem 1rem;
		color: var(--color-muted);
	}

	.welcome h1 {
		font-size: 1.5rem;
		color: var(--color-text);
		margin-bottom: 0.5rem;
	}

	/* Messages */
	.message {
		margin-bottom: 1.25rem;
		max-width: 720px;
	}

	.message-label {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--color-muted);
		margin-bottom: 0.25rem;
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}

	.message-content {
		font-size: 0.9375rem;
		line-height: 1.6;
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.message.human .message-content {
		background: #eff6ff;
		padding: 0.75rem 1rem;
		border-radius: 8px;
	}

	.message.ai .message-content {
		padding: 0.75rem 0;
	}

	.thinking {
		color: var(--color-muted);
		font-style: italic;
	}

	/* Sources */
	.sources {
		margin-top: 0.5rem;
		font-size: 0.8125rem;
	}

	.sources summary {
		cursor: pointer;
		color: var(--color-primary);
		font-weight: 500;
	}

	.sources ul {
		list-style: none;
		margin-top: 0.5rem;
		padding: 0;
	}

	.sources li {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: 6px;
		margin-bottom: 0.5rem;
	}

	.sources li strong {
		font-size: 0.8125rem;
	}

	.excerpt {
		font-size: 0.75rem;
		color: var(--color-muted);
		margin-top: 0.25rem;
		line-height: 1.4;
	}

	/* Input Area */
	.input-area {
		display: flex;
		gap: 0.75rem;
		padding: 1rem 1.5rem;
		border-top: 1px solid var(--color-border);
	}

	.input-area input {
		flex: 1;
		padding: 0.625rem 1rem;
		border: 1px solid var(--color-border);
		border-radius: 8px;
		font-size: 0.9375rem;
		outline: none;
	}

	.input-area input:focus {
		border-color: var(--color-primary);
		box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
	}

	.input-area button {
		padding: 0.625rem 1.5rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 0.9375rem;
		cursor: pointer;
		white-space: nowrap;
	}

	.input-area button:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	.input-area button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>
