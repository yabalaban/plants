<script lang="ts">
    import '../app.css';
    import { page } from '$app/stores';

    let { children } = $props();

    let path = $derived($page.url.pathname);
</script>

<svelte:head>
    <link rel="icon" href="/favicon.svg" />
</svelte:head>

<div class="app">
    <main>
        {@render children()}
    </main>

    <nav class="bottom-nav">
        <a href="/" class:active={path === '/'}>
            <span class="icon">🏠</span>
            <span class="label">Home</span>
        </a>
        <a href="/add" class:active={path === '/add'}>
            <span class="icon">➕</span>
            <span class="label">Add</span>
        </a>
        <a href="/settings" class:active={path === '/settings'}>
            <span class="icon">⚙️</span>
            <span class="label">Settings</span>
        </a>
    </nav>
</div>

<style>
    .app { min-height: 100dvh; display: flex; flex-direction: column; max-width: 480px; margin: 0 auto; }
    main { flex: 1; padding: 1rem; padding-bottom: calc(4rem + env(safe-area-inset-bottom, 0px)); }
    .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; display: flex; justify-content: space-around; background: var(--surface); border-top: 1px solid var(--border); padding: 0.5rem 0; padding-bottom: calc(0.5rem + env(safe-area-inset-bottom, 0px)); z-index: 100; }
    .bottom-nav a { display: flex; flex-direction: column; align-items: center; gap: 0.2rem; text-decoration: none; color: var(--text-muted); font-size: 0.7rem; padding: 0.3rem 1rem; transition: color 0.15s; }
    .bottom-nav a.active { color: var(--green); }
    .icon { font-size: 1.3rem; }
</style>
