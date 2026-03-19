<script lang="ts">
    import '../app.css';
    import { page } from '$app/stores';

    let { children } = $props();

    let path = $derived($page.url.pathname);

    const navItems = [
        { href: '/', label: 'Home', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
        { href: '/add', label: 'Add', icon: 'M12 4v16m8-8H4' },
        { href: '/settings', label: 'Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
    ];
</script>

<div class="app">
    <main>
        {@render children()}
    </main>

    <nav class="bottom-nav" role="navigation" aria-label="Main navigation">
        <div class="nav-inner">
            {#each navItems as item}
                {@const active = item.href === '/' ? path === '/' : path.startsWith(item.href)}
                <a href={item.href} class="nav-item" class:active aria-current={active ? 'page' : undefined}>
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d={item.icon} />
                    </svg>
                    <span class="nav-label">{item.label}</span>
                    {#if active}
                        <span class="nav-dot"></span>
                    {/if}
                </a>
            {/each}
        </div>
    </nav>
</div>

<style>
    .app {
        min-height: 100dvh;
        display: flex;
        flex-direction: column;
        max-width: 480px;
        margin: 0 auto;
        position: relative;
    }

    main {
        flex: 1;
        padding: 1.25rem;
        padding-top: calc(1.25rem + env(safe-area-inset-top, 0px));
        padding-bottom: calc(5.5rem + env(safe-area-inset-bottom, 0px));
    }

    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 100;
        background: linear-gradient(to top, var(--bg) 60%, transparent);
        padding-top: 1.5rem;
    }

    .nav-inner {
        display: flex;
        justify-content: space-around;
        align-items: center;
        max-width: 480px;
        margin: 0 auto;
        background: var(--surface-raised);
        border: 1px solid var(--border);
        border-bottom: none;
        border-radius: var(--radius) var(--radius) 0 0;
        padding: 0.5rem 0.75rem;
        padding-bottom: calc(0.5rem + env(safe-area-inset-bottom, 0px));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }

    .nav-item {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.15rem;
        text-decoration: none;
        color: var(--text-muted);
        padding: 0.6rem 1.5rem;
        border-radius: var(--radius-sm);
        transition: color 0.25s var(--ease-out), background 0.25s var(--ease-out);
        min-height: 48px;
        justify-content: center;
    }

    .nav-item:active {
        transform: scale(0.92);
        transition: transform 0.1s;
    }

    .nav-item.active {
        color: var(--accent);
        background: var(--accent-dim);
    }

    .nav-icon {
        width: 22px;
        height: 22px;
    }

    .nav-label {
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .nav-dot {
        position: absolute;
        bottom: 4px;
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: var(--accent);
    }
</style>
