<script lang="ts">
    import { onMount } from 'svelte';
    import { getSettings, updateSettings, testTelegram } from '$lib/api';
    import type { Settings } from '$lib/types';

    let settings = $state<Settings | null>(null);
    let loading = $state(true);
    let saving = $state(false);
    let testing = $state(false);
    let message = $state<{ text: string; type: 'success' | 'error' } | null>(null);

    let city = $state('');
    let botToken = $state('');
    let chatId = $state('');
    let reminderTime = $state('');

    let canTest = $derived(
        settings?.telegram_bot_token_set === true || botToken.trim().length > 0
    );

    async function load() {
        try {
            loading = true;
            settings = await getSettings();
            city = settings.location_city ?? '';
            chatId = settings.telegram_chat_id ?? '';
            reminderTime = settings.reminder_time ?? '09:00';
        } catch {
            showMessage('Failed to load settings', 'error');
        } finally {
            loading = false;
        }
    }

    async function handleSave(event: Event) {
        event.preventDefault();
        saving = true;
        try {
            const update: Record<string, string> = {
                location_city: city.trim(),
                telegram_chat_id: chatId.trim(),
                reminder_time: reminderTime,
            };
            if (botToken.trim()) update.telegram_bot_token = botToken.trim();

            settings = await updateSettings(update);
            botToken = '';
            showMessage('Settings saved', 'success');
        } catch {
            showMessage('Failed to save settings', 'error');
        } finally {
            saving = false;
        }
    }

    async function handleTest() {
        if (!canTest || testing) return;
        testing = true;
        try {
            await testTelegram();
            showMessage('Test message sent!', 'success');
        } catch {
            showMessage('Failed to send test message', 'error');
        } finally {
            testing = false;
        }
    }

    function showMessage(text: string, type: 'success' | 'error') {
        message = { text, type };
        setTimeout(() => { message = null; }, 3000);
    }

    onMount(load);
</script>

<div class="page">
    <header class="page-header">
        <a href="/" class="back-link" aria-label="Back to garden">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="back-icon">
                <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
        </a>
        <h1 class="page-title">Settings</h1>
    </header>

    {#if loading}
        <div class="skeleton-form">
            {#each [1, 2, 3] as _}
                <div class="skeleton-field"></div>
            {/each}
        </div>
    {:else}
        <form onsubmit={handleSave} class="form">
            <div class="card">
                <div class="card-header">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="card-icon">
                        <path d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <div>
                        <h2 class="card-title">Location</h2>
                        <p class="card-desc">For weather-based watering adjustments</p>
                    </div>
                </div>
                <div class="field">
                    <label class="field-label" for="city">City</label>
                    <input id="city" type="text" placeholder="e.g. London" bind:value={city} disabled={saving} />
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="card-icon">
                        <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    <div>
                        <h2 class="card-title">Telegram</h2>
                        <p class="card-desc">Daily watering reminders</p>
                    </div>
                </div>
                <div class="field">
                    <label class="field-label" for="bot-token">
                        Bot Token
                        {#if settings?.telegram_bot_token_set}
                            <span class="badge">Active</span>
                        {/if}
                    </label>
                    <input
                        id="bot-token"
                        type="password"
                        placeholder={settings?.telegram_bot_token_set ? 'Enter new token to replace' : 'Paste bot token'}
                        bind:value={botToken}
                        disabled={saving}
                        autocomplete="off"
                    />
                </div>
                <div class="field">
                    <label class="field-label" for="chat-id">Chat ID</label>
                    <input id="chat-id" type="text" placeholder="e.g. 123456789" bind:value={chatId} disabled={saving} />
                </div>
                {#if canTest}
                    <button
                        type="button"
                        class="test-btn"
                        onclick={handleTest}
                        disabled={testing}
                    >
                        {#if testing}
                            <span class="spinner"></span>
                            Sending...
                        {:else}
                            Send Test Message
                        {/if}
                    </button>
                {/if}
            </div>

            <div class="card">
                <div class="card-header">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="card-icon">
                        <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                        <h2 class="card-title">Reminder</h2>
                        <p class="card-desc">When to send daily notifications</p>
                    </div>
                </div>
                <div class="field">
                    <label class="field-label" for="reminder-time">Time</label>
                    <input id="reminder-time" type="time" bind:value={reminderTime} disabled={saving} />
                </div>
            </div>

            {#if message}
                <div class="toast {message.type}" style="animation: fadeIn 0.3s var(--ease-out)">
                    {message.text}
                </div>
            {/if}

            <button type="submit" class="save-btn" disabled={saving}>
                {#if saving}
                    <span class="spinner"></span>
                    Saving...
                {:else}
                    Save Settings
                {/if}
            </button>

            <a href="/settings/debug" class="debug-link">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="debug-icon">
                    <path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                Debug
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chevron"><path d="M9 18l6-6-6-6"/></svg>
            </a>
        </form>
    {/if}
</div>

<style>
    .page {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        animation: fadeIn 0.4s var(--ease-out);
    }

    .page-header { display: flex; align-items: center; gap: 0.75rem; }
    .back-link {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--surface);
        color: var(--text-secondary);
        text-decoration: none;
    }
    .back-icon { width: 20px; height: 20px; }
    .page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; }

    .skeleton-form { display: flex; flex-direction: column; gap: 1rem; }
    .skeleton-field { height: 100px; border-radius: var(--radius); background: var(--surface); animation: pulse 1.5s infinite; }

    .form { display: flex; flex-direction: column; gap: 1rem; }

    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .card-header { display: flex; gap: 0.75rem; align-items: flex-start; }
    .card-icon { width: 22px; height: 22px; color: var(--accent); flex-shrink: 0; margin-top: 0.15rem; }
    .card-title { font-family: var(--font-display); font-size: 1.05rem; font-weight: 700; }
    .card-desc { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.1rem; }

    .field { display: flex; flex-direction: column; gap: 0.35rem; }
    .field-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .badge {
        font-size: 0.6rem;
        padding: 0.15rem 0.45rem;
        border-radius: 999px;
        background: var(--accent-dim);
        color: var(--accent);
        border: 1px solid var(--accent-medium);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .test-btn {
        padding: 0.75rem;
        background: var(--surface-raised);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        font-weight: 600;
        font-size: 0.875rem;
        color: var(--text-secondary);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        min-height: 48px;
        transition: border-color 0.15s;
    }
    .test-btn:active { border-color: var(--accent); }
    .test-btn:disabled { opacity: 0.5; }

    .toast {
        padding: 0.75rem 1rem;
        border-radius: var(--radius-sm);
        font-size: 0.85rem;
        font-weight: 500;
        text-align: center;
    }
    .toast.success { background: var(--accent-dim); color: var(--accent); border: 1px solid var(--accent-medium); }
    .toast.error { background: var(--danger-dim); color: var(--danger); border: 1px solid rgba(201, 123, 123, 0.2); }

    .save-btn {
        padding: 1rem;
        background: var(--accent);
        color: var(--bg);
        border-radius: var(--radius-sm);
        font-weight: 700;
        font-size: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        min-height: 52px;
        transition: transform 0.15s var(--ease-spring);
    }
    .save-btn:active { transform: scale(0.97); }
    .save-btn:disabled { opacity: 0.5; }

    .spinner {
        width: 1rem;
        height: 1rem;
        border: 2px solid rgba(0,0,0,0.15);
        border-top-color: var(--bg);
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }

    .debug-link {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 1rem 1.25rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        color: var(--text-muted);
        text-decoration: none;
        font-size: 0.875rem;
        font-weight: 500;
        transition: border-color 0.15s;
    }
    .debug-link:hover { border-color: var(--accent-medium); }
    .debug-icon { width: 18px; height: 18px; }
    .chevron { width: 16px; height: 16px; margin-left: auto; opacity: 0.4; }
</style>
