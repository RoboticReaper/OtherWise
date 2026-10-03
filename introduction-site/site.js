
/* Presentation interactions only. No tracking, browsing data, or backend requests. */
(() => {
  const paths = {
    ai: { start: 'AI tools', bridge: 'Human–AI interaction', destination: 'Psychology', description: 'How we work with AI leads to questions about attention, judgment, and human behavior.' },
    design: { start: 'Design', bridge: 'Accessible design', destination: 'Human perception', description: 'Designing for different abilities opens questions about how people see, hear, and understand the world.' },
    music: { start: 'Music', bridge: 'Sound and emotion', destination: 'Neuroscience', description: 'The way music changes how we feel leads to questions about memory, emotion, and the brain.' }
  };
  document.querySelectorAll('[data-topic]').forEach(button => {
    button.addEventListener('click', () => {
      const path = paths[button.dataset.topic];
      document.querySelectorAll('[data-topic]').forEach(item => {
        const active = item === button;
        item.classList.toggle('active', active);
        item.setAttribute('aria-pressed', String(active));
      });
      Object.entries(path).forEach(([key, value]) => {
        const element = document.querySelector(`[data-journey="${key}"]`);
        if (element) element.textContent = value;
      });
    });
  });
  document.querySelectorAll('[data-match]').forEach(button => {
    button.addEventListener('click', () => {
      const image = document.getElementById('matching-image');
      if (!image) return;
      const context = button.dataset.match === 'context';
      image.src = context ? './assets/context-matching.png' : './assets/basic-matching.png';
      image.alt = context ? 'Context-based project diagram connecting computer science to psychology through human–computer interaction.' : 'Basic matching project diagram showing a less direct bridge from computer science to psychology.';
      document.querySelectorAll('[data-match]').forEach(item => {
        const active = item === button;
        item.classList.toggle('active', active);
        item.setAttribute('aria-pressed', String(active));
      });
    });
  });
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.body.classList.add('js-enabled');
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.05 });
    document.querySelectorAll('.reveal').forEach(element => observer.observe(element));
  }
})();
