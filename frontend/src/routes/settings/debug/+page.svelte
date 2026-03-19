<script lang="ts">
    import { onMount } from 'svelte';
    import { getWeatherCache, getClaudeLogs } from '$lib/api';
    import type { WeatherEntry, ClaudeLog } from '$lib/types';

    let weather = $state<WeatherEntry[]>([]);
    let logs = $state<ClaudeLog[]>([]);
    let loading = $state(true);
    let activeTab = $state<'weather' | 'claude'>('claude');
    let expandedLog = $state<number | null>(null);

    function toggleLog(id: number) {
        expandedLog = expandedLog === id ? null : id;
    }

    function formatDuration(ms: number): string {
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    }

    function formatDate(iso: string): string {
        return new Date(iso + 'Z').toLocaleString(undefined, {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    }

    function todayStr(): string {
        const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    }

    function isForecast(date: string): boolean {
        return date > todayStr();
    }

    function tryParseJson(s: string): string {
        try {
            return JSON.stringify(JSON.parse(s), null, 2);
        } catch {
            return s;
        }
    }

    async function load() {
        loading = true;
        try {
            [weather, logs] = await Promise.all([getWeatherCache(), getClaudeLogs()]);
        } catch {
            // silently fail
        } finally {
            loading = false;
        }
    }

    onMount(load);
</script>

<div class="page">
    <header class="page-header">
        <a href="/settings" class="back-link" aria-label="Back to settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="back-icon">
                <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
        </a>
        <h1 class="page-title">Debug</h1>
    </header>

    <div class="tabs">
        <button class="tab" class:active={activeTab === 'claude'} onclick={() => activeTab = 'claude'}>
            Claude Logs
        </button>
        <button class="tab" class:active={activeTab === 'weather'} onclick={() => activeTab = 'weather'}>
            Weather Cache
        </button>
    </div>

    {#if loading}
        <div class="skeleton-list">
            {#each [1, 2, 3] as _}
                <div class="skeleton-row"></div>
            {/each}
        </div>
    {:else if activeTab === 'claude'}
        {#if logs.length === 0}
            <div class="empty">No Claude calls logged yet</div>
        {:else}
            <div class="log-list">
                {#each logs as log}
                    <button class="log-entry" class:expanded={expandedLog === log.id} onclick={() => toggleLog(log.id)}>
                        <div class="log-header">
                            <div class="log-meta">
                                <span class="log-task">{log.task}</span>
                                <span class="log-duration">{formatDuration(log.duration_ms)}</span>
                                {#if log.error}
                                    <span class="log-badge error">error</span>
                                {:else}
                                    <span class="log-badge success">ok</span>
                                {/if}
                            </div>
                            <span class="log-date">{formatDate(log.created_at)}</span>
                        </div>

                        {#if expandedLog === log.id}
                            <!-- svelte-ignore a11y_click_events_have_key_events -->
                            <div class="log-detail" onclick={(e) => e.stopPropagation()}>
                                <div class="detail-section">
                                    <div class="detail-label">Prompt</div>
                                    <pre class="detail-content">{log.prompt}</pre>
                                </div>
                                {#if log.response}
                                    <div class="detail-section">
                                        <div class="detail-label">Response</div>
                                        <pre class="detail-content">{tryParseJson(log.response)}</pre>
                                    </div>
                                {/if}
                                {#if log.error}
                                    <div class="detail-section">
                                        <div class="detail-label">Error</div>
                                        <pre class="detail-content error-text">{log.error}</pre>
                                    </div>
                                {/if}
                            </div>
                        {/if}
                    </button>
                {/each}
            </div>
        {/if}
    {:else}
        {#if weather.length === 0}
            <div class="empty">No weather data cached yet</div>
        {:else}
            <div class="weather-list">
                {#each weather as w}
                    <div class="weather-row" class:forecast={isForecast(w.date)}>
                        <span class="weather-date">
                            {w.date}
                            {#if isForecast(w.date)}
                                <span class="forecast-badge">forecast</span>
                            {/if}
                        </span>
                        <div class="weather-stats">
                            {#if w.temp_high != null}
                                <span class="weather-stat" title="High">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="stat-icon hot"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
                                    {w.temp_high.toFixed(1)}°
                                </span>
                            {/if}
                            {#if w.temp_low != null}
                                <span class="weather-stat" title="Low">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="stat-icon cold"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>
                                    {w.temp_low.toFixed(1)}°
                                </span>
                            {/if}
                            {#if w.humidity != null}
                                <span class="weather-stat" title="Humidity">{w.humidity.toFixed(0)}%</span>
                            {/if}
                            {#if w.precipitation_mm != null && w.precipitation_mm > 0}
                                <span class="weather-stat rain" title="Precipitation">{w.precipitation_mm.toFixed(1)}mm</span>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    {/if}
</div>

<style>
    .page {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        animation: fadeIn 0.4s var(--ease-out);
    }

    .page-header { display: flex; align-items: center; gap: 0.75rem; }
    .back-link {
        display: flex; align-items: center; justify-content: center;
        width: 40px; height: 40px; border-radius: 50%;
        background: var(--surface); color: var(--text-secondary); text-decoration: none;
    }
    .back-icon { width: 20px; height: 20px; }
    .page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; }

    .tabs {
        display: flex; gap: 0.5rem;
        background: var(--surface); border-radius: var(--radius-sm);
        padding: 0.25rem; border: 1px solid var(--border);
    }
    .tab {
        flex: 1; padding: 0.6rem; border-radius: var(--radius-xs);
        font-size: 0.8rem; font-weight: 600; color: var(--text-muted);
        background: transparent; transition: all 0.15s;
    }
    .tab.active { background: var(--surface-raised); color: var(--text-primary); }

    .skeleton-list { display: flex; flex-direction: column; gap: 0.5rem; }
    .skeleton-row { height: 60px; border-radius: var(--radius-sm); background: var(--surface); animation: pulse 1.5s infinite; }

    .empty {
        text-align: center; padding: 3rem 1rem;
        color: var(--text-muted); font-size: 0.9rem;
    }

    /* Claude logs */
    .log-list { display: flex; flex-direction: column; gap: 0.5rem; }
    .log-entry {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-sm); padding: 0.85rem 1rem;
        text-align: left; width: 100%; cursor: pointer;
        transition: border-color 0.15s;
    }
    .log-entry:hover { border-color: var(--accent-medium); }
    .log-entry.expanded { border-color: var(--accent); }

    .log-header { display: flex; flex-direction: column; gap: 0.35rem; }
    .log-meta { display: flex; align-items: center; gap: 0.5rem; }
    .log-task {
        font-weight: 600; font-size: 0.85rem;
        color: var(--text-primary); font-family: var(--font-display);
    }
    .log-duration { font-size: 0.75rem; color: var(--text-muted); font-variant-numeric: tabular-nums; }
    .log-date { font-size: 0.7rem; color: var(--text-muted); }

    .log-badge {
        font-size: 0.6rem; padding: 0.1rem 0.4rem; border-radius: 999px;
        font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .log-badge.success { background: var(--accent-dim); color: var(--accent); border: 1px solid var(--accent-medium); }
    .log-badge.error { background: var(--danger-dim); color: var(--danger); border: 1px solid rgba(201, 123, 123, 0.2); }

    .log-detail {
        margin-top: 0.75rem; padding-top: 0.75rem;
        border-top: 1px solid var(--border);
        display: flex; flex-direction: column; gap: 0.75rem;
    }
    .detail-section { display: flex; flex-direction: column; gap: 0.25rem; }
    .detail-label {
        font-size: 0.65rem; font-weight: 600; color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .detail-content {
        font-size: 0.75rem; line-height: 1.5; color: var(--text-secondary);
        background: var(--bg); border-radius: var(--radius-xs);
        padding: 0.6rem; overflow-x: auto; white-space: pre-wrap;
        word-break: break-word; margin: 0; font-family: 'DM Sans', monospace;
    }
    .error-text { color: var(--danger); }

    /* Weather */
    .weather-list { display: flex; flex-direction: column; gap: 0.35rem; }
    .weather-row {
        display: flex; justify-content: space-between; align-items: center;
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-sm); padding: 0.75rem 1rem;
    }
    .weather-date { font-weight: 600; font-size: 0.85rem; font-variant-numeric: tabular-nums; }
    .weather-stats { display: flex; gap: 0.75rem; align-items: center; }
    .weather-stat {
        font-size: 0.8rem; color: var(--text-secondary);
        display: flex; align-items: center; gap: 0.2rem;
        font-variant-numeric: tabular-nums;
    }
    .stat-icon { width: 14px; height: 14px; }
    .stat-icon.hot { color: var(--alert); }
    .stat-icon.cold { color: var(--info); }
    .weather-stat.rain { color: var(--info); }
    .weather-row.forecast { opacity: 0.65; border-style: dashed; }
    .forecast-badge {
        font-size: 0.55rem; padding: 0.1rem 0.35rem; border-radius: 999px;
        background: var(--info-dim, rgba(123, 168, 201, 0.1)); color: var(--info);
        border: 1px solid rgba(123, 168, 201, 0.2);
        font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
        margin-left: 0.4rem; vertical-align: middle;
    }
</style>
