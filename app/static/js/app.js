// Minimal UI helpers
(function(){
  // Auto theme: follow OS. Bootstrap 5.3 supports data-bs-theme.
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
  function apply(){
    document.documentElement.setAttribute('data-bs-theme', prefersDark && prefersDark.matches ? 'dark' : 'light');
  }
  apply();
  if (prefersDark && prefersDark.addEventListener) prefersDark.addEventListener('change', apply);
})();
