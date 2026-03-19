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
            const update: Record<string, string> = {};
            if (city.trim()) update.location_city = city.trim();
            if (botToken.trim()) update.telegram_bot_token = botToken.trim();
            if (chatId.trim()) update.telegram_chat_id = chatId.trim();
            if (reminderTime) update.reminder_time = reminderTime;

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
    <h1 class="title">Settings</h1>

    {#if loading}
        <div class="state-box">Loading...</div>
    {:else}
        <form onsubmit={handleSave} class="form">
            <div class="section">
                <h2 class="section-title">Location</h2>
                <p class="section-desc">Used to fetch local weather for watering adjustments.</p>
                <div class="field">
                    <label for="city">City</label>
                    <input
                        id="city"
                        type="text"
                        placeholder="e.g. San Francisco"
                        bind:value={city}
                        disabled={saving}
                    />
                </div>
            </div>

            <div class="divider"></div>

            <div class="section">
                <h2 class="section-title">Telegram Notifications</h2>
                <p class="section-desc">Receive watering reminders via Telegram bot.</p>

                <div class="field">
                    <label for="bot-token">
                        Bot Token
                        {#if settings?.telegram_bot_token_set}
                            <span class="badge configured">Configured</span>
                        {/if}
                    </label>
                    <input
                        id="bot-token"
                        type="password"
                        placeholder={settings?.telegram_bot_token_set ? 'Enter new token to replace' : 'e.g. 123456:ABC-DEF...'}
                        bind:value={botToken}
                        disabled={saving}
                        autocomplete="off"
                    />
                </div>

                <div class="field">
                    <label for="chat-id">Chat ID</label>
                    <input
                        id="chat-id"
                        type="text"
                        placeholder="e.g. 123456789"
                        bind:value={chatId}
                        disabled={saving}
                    />
                </div>
            </div>

            <div class="divider"></div>

            <div class="section">
                <h2 class="section-title">Reminder Time</h2>
                <div class="field">
                    <label for="reminder-time">Daily reminder at</label>
                    <input
                        id="reminder-time"
                        type="time"
                        bind:value={reminderTime}
                        disabled={saving}
                    />
                </div>
            </div>

            {#if message}
                <div class="message {message.type}">{message.text}</div>
            {/if}

            <div class="actions">
                <button type="submit" class="save-btn" disabled={saving}>
                    {saving ? 'Saving...' : 'Save Settings'}
                </button>
                <button
                    type="button"
                    class="test-btn"
                    onclick={handleTest}
                    disabled={!canTest || testing}
                >
                    {testing ? 'Sending...' : 'Test Telegram'}
                </button>
            </div>
        </form>
    {/if}
</div>

<style>
    .page { display: flex; flex-direction: column; gap: 1.5rem; }
    .title { font-size: 1.6rem; font-weight: 700; }

    .state-box { padding: 2rem; text-align: center; color: var(--text-muted); background: var(--surface); border-radius: var(--radius); }

    .form { display: flex; flex-direction: column; gap: 1.25rem; }

    .section { display: flex; flex-direction: column; gap: 0.75rem; }
    .section-title { font-size: 1rem; font-weight: 700; }
    .section-desc { font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; }

    .divider { height: 1px; background: var(--border); }

    .field { display: flex; flex-direction: column; gap: 0.4rem; }
    .field label { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: flex; align-items: center; gap: 0.5rem; }

    .badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 999px; }
    .badge.configured { background: var(--green-bg); color: var(--green); border: 1px solid rgba(74, 222, 128, 0.3); }

    .message { padding: 0.75rem 1rem; border-radius: var(--radius-sm); font-size: 0.875rem; }
    .message.success { background: var(--green-bg); color: var(--green); border: 1px solid rgba(74, 222, 128, 0.3); }
    .message.error { background: var(--red-bg); color: var(--red); border: 1px solid rgba(239, 68, 68, 0.3); }

    .actions { display: flex; flex-direction: column; gap: 0.75rem; }
    .save-btn { padding: 0.875rem; background: var(--green); color: #000; border-radius: var(--radius-sm); font-weight: 600; font-size: 1rem; transition: opacity 0.15s; }
    .save-btn:disabled { opacity: 0.5; }
    .test-btn { padding: 0.75rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-weight: 500; transition: opacity 0.15s; }
    .test-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
