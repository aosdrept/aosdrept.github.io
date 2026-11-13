/* Progressive enhancement: both languages and all content work without JS. */
(() => {
  const header = document.querySelector('.site-header');
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#main-nav');
  const mobile = window.matchMedia('(max-width: 760px)');

  function setMenu(open) {
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? menu.dataset.closeLabel : menu.dataset.openLabel);
    header.classList.toggle('menu-open', open);
    nav.hidden = mobile.matches && !open;
  }
  menu.hidden = false;
  header.classList.add('enhanced');
  setMenu(false);
  menu.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
  nav.addEventListener('click', (event) => {
    if (event.target.closest('a') && mobile.matches) {
      const target = document.querySelector(event.target.closest('a').hash);
      setMenu(false);
      if (target) {
        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      }
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      menu.focus();
    }
  });
  mobile.addEventListener('change', () => setMenu(false));

  // Keep the same section when moving between the two language URLs.
  const languageLinks = document.querySelectorAll('.language-switch a');
  const updateLanguageLinks = () => {
    languageLinks.forEach((link) => {
      const url = new URL(link.href);
      url.hash = location.hash;
      link.href = url.href;
    });
  };
  updateLanguageLinks();
  window.addEventListener('hashchange', updateLanguageLinks);

  // Highlight the section currently being read without altering browser history.
  const links = [...nav.querySelectorAll('a')];
  const sections = links.map(link => document.querySelector(link.hash));
  let queued = false;
  const updateActiveLink = () => {
    const offset = header.offsetHeight + 100;
    let active = null;
    sections.forEach(section => {
      if (section.getBoundingClientRect().top <= offset) active = section.id;
    });
    links.forEach(link => {
      if (link.hash === '#' + active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    queued = false;
  };
  window.addEventListener('scroll', () => {
    if (!queued) {
      queued = true;
      window.requestAnimationFrame(updateActiveLink);
    }
  }, { passive: true });
  updateActiveLink();
})();
