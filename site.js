/* Optional enhancements. All content and links remain available without JS. */
(() => {
  const header = document.querySelector(".site-header");
  if (!header) return;

  // Match the navigation breakpoint in style.css.
  const compactLayout = window.matchMedia("(max-width: 70rem)");
  const menuButton = header.querySelector(".menu-toggle");
  const navigation = header.querySelector("#main-nav");
  const headerTools = header.querySelector(".header-tools");

  // Keep anchor targets and keyboard focus clear of the sticky desktop header.
  function updateHeaderOffset() {
    const isSticky = window.getComputedStyle(header).position === "sticky";
    const offset = isSticky ? header.getBoundingClientRect().height + 16 : 16;
    document.documentElement.style.setProperty(
      "--header-offset",
      `${offset}px`,
    );
  }

  updateHeaderOffset();
  window.addEventListener("resize", updateHeaderOffset);
  if ("ResizeObserver" in window) {
    new ResizeObserver(updateHeaderOffset).observe(header);
  }

  // Disclosure navigation: the toggle keeps focus; Tab reaches the open links.
  if (menuButton && navigation && headerTools) {
    function setMenu(open) {
      const expanded = compactLayout.matches && open;
      menuButton.setAttribute("aria-expanded", String(expanded));
      menuButton.setAttribute(
        "aria-label",
        expanded ? menuButton.dataset.closeLabel : menuButton.dataset.openLabel,
      );
      navigation.hidden = compactLayout.matches && !expanded;
    }

    function updateNavigationLayout() {
      const focusedElement = document.activeElement;

      // Match DOM/tab order to the visible layout at each breakpoint.
      if (compactLayout.matches) {
        header.append(navigation);
      } else {
        header.insertBefore(navigation, headerTools);
      }

      menuButton.hidden = !compactLayout.matches;
      setMenu(false);
      if (compactLayout.matches && navigation.contains(focusedElement)) {
        menuButton.focus({ preventScroll: true });
      } else if (!compactLayout.matches && focusedElement === menuButton) {
        navigation.querySelector("a").focus({ preventScroll: true });
      } else if (navigation.contains(focusedElement)) {
        // Reparenting a focused link can reset focus in some browsers.
        focusedElement.focus({ preventScroll: true });
      }
      updateHeaderOffset();
    }

    updateNavigationLayout();
    compactLayout.addEventListener("change", updateNavigationLayout);
    menuButton.addEventListener("click", () => {
      setMenu(menuButton.getAttribute("aria-expanded") !== "true");
    });

    navigation.addEventListener("click", (event) => {
      const link = event.target.closest("a");
      if (!link || !compactLayout.matches) return;
      const target = document.getElementById(link.hash.slice(1));
      setMenu(false);
      if (target) {
        target.setAttribute("tabindex", "-1");
        target.focus({ preventScroll: true });
      }
    });

    header.addEventListener("keydown", (event) => {
      if (
        event.key === "Escape" &&
        menuButton.getAttribute("aria-expanded") === "true"
      ) {
        setMenu(false);
        menuButton.focus();
      }
    });

    // Mark the section being read. No history entries or scroll interception.
    const links = [...navigation.querySelectorAll("a")];
    const sections = links.map((link) =>
      document.getElementById(link.hash.slice(1)),
    );
    let scrollUpdatePending = false;

    function updateActiveSection() {
      const stickyHeight =
        window.getComputedStyle(header).position === "sticky"
          ? header.getBoundingClientRect().height
          : 0;
      let activeSection = null;
      sections.forEach((section) => {
        if (
          section &&
          section.getBoundingClientRect().top <= stickyHeight + 100
        ) {
          activeSection = section.id;
        }
      });
      links.forEach((link) => {
        if (link.hash === `#${activeSection}`) {
          link.setAttribute("aria-current", "location");
        } else {
          link.removeAttribute("aria-current");
        }
      });
      scrollUpdatePending = false;
    }

    window.addEventListener(
      "scroll",
      () => {
        if (!scrollUpdatePending) {
          scrollUpdatePending = true;
          window.requestAnimationFrame(updateActiveSection);
        }
      },
      { passive: true },
    );
    window.addEventListener("resize", updateActiveSection);
    updateActiveSection();
  }

  // Equivalent sections share IDs in both languages, including legal pages.
  const languageLinks = header.querySelectorAll(".language-switch a");
  function updateLanguageLinks() {
    languageLinks.forEach((link) => {
      const url = new URL(link.href);
      url.hash = window.location.hash;
      link.href = url.href;
    });
  }
  updateLanguageLinks();
  window.addEventListener("hashchange", updateLanguageLinks);
})();
