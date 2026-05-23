(() => {
  const INSTALL_DISMISS_KEY = 'pwa-install-dismissed';
  const installBanner = document.getElementById('pwa-install');
  const updateBanner = document.getElementById('pwa-update');
  const offlineBanner = document.getElementById('pwa-offline');
  let deferredPrompt = null;

  function show(el) {
    if (el) {
      el.hidden = false;
    }
  }

  function hide(el) {
    if (el) {
      el.hidden = true;
    }
  }

  function setOfflineState(isOffline) {
    document.documentElement.classList.toggle('is-offline', isOffline);
    if (offlineBanner) {
      offlineBanner.hidden = !isOffline;
    }
  }

  function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      return;
    }

    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .then((registration) => {
        if (registration.waiting) {
          show(updateBanner);
        }

        registration.addEventListener('updatefound', () => {
          const worker = registration.installing;
          if (!worker) {
            return;
          }
          worker.addEventListener('statechange', () => {
            if (worker.state === 'installed' && navigator.serviceWorker.controller) {
              show(updateBanner);
            }
          });
        });
      })
      .catch(() => {});

    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload();
    });
  }

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    if (localStorage.getItem(INSTALL_DISMISS_KEY) === '1') {
      return;
    }
    deferredPrompt = event;
    show(installBanner);
  });

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    hide(installBanner);
    localStorage.removeItem(INSTALL_DISMISS_KEY);
  });

  installBanner?.querySelector('[data-pwa-install]')?.addEventListener('click', async () => {
    if (!deferredPrompt) {
      return;
    }
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    hide(installBanner);
  });

  installBanner?.querySelector('[data-pwa-dismiss]')?.addEventListener('click', () => {
    localStorage.setItem(INSTALL_DISMISS_KEY, '1');
    hide(installBanner);
  });

  updateBanner?.querySelector('[data-pwa-update]')?.addEventListener('click', () => {
    navigator.serviceWorker.getRegistration().then((registration) => {
      registration?.waiting?.postMessage({ type: 'SKIP_WAITING' });
    });
  });

  updateBanner?.querySelector('[data-pwa-update-dismiss]')?.addEventListener('click', () => {
    hide(updateBanner);
  });

  window.addEventListener('online', () => setOfflineState(false));
  window.addEventListener('offline', () => setOfflineState(true));
  setOfflineState(!navigator.onLine);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', registerServiceWorker);
  } else {
    registerServiceWorker();
  }
})();
