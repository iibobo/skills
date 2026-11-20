// Portable symbolic navigation metadata; the local IDEA plugin owns transport and authorization.
function linkDiagramSources(svg) {
  const data = document.getElementById('source-map');
  if (!data) return;
  const locations = JSON.parse(data.textContent);
  const normalize = value => (value.trim().match(/^[+\-#~]?\s*([\w$]+\([^)]*\))/)?.[1] || value.trim()).replace(/\s/g, '');
  function link(text, location, owner, label) {
    const className = location?.className || owner?.className;
    const symbolic = className && (!location?.methodName || Array.isArray(location.parameterTypes));
    const local = location?.file && Number.isInteger(location.line) && location.line > 0;
    if (!symbolic && !local) return;
    const anchor = document.createElementNS('http://www.w3.org/2000/svg', 'a');
    anchor.setAttribute('class', 'source-link');
    anchor.setAttribute('role', 'link');
    anchor.setAttribute('tabindex', '0');
    anchor.setAttribute('aria-label', label + '，在 IDEA 中定位源码');
    if (symbolic) anchor.dataset.ideaTarget = JSON.stringify({className,
      ...(location.methodName ? {methodName: location.methodName, parameterTypes: location.parameterTypes} : {})});
    if (!symbolic && local) {
      const url = new URL(location.file, document.baseURI);
      if (url.protocol === 'file:') anchor.setAttribute('href', 'idea://open?file=' + encodeURIComponent(decodeURIComponent(url.pathname)) + '&line=' + location.line);
    }
    anchor.addEventListener('click', event => {
      if (anchor.hasAttribute('href')) return;
      event.preventDefault();
      if (document.documentElement.dataset.ideaBridgeReady === 'true') return;
      let notice = document.getElementById('source-navigation-hint');
      if (!notice) {
        notice = document.createElement('div'); notice.id = 'source-navigation-hint'; notice.setAttribute('role', 'status');
        if (!document.getElementById('source-navigation-hint-style')) {
          const style = document.createElement('style'); style.id = 'source-navigation-hint-style';
          style.textContent = `
            #source-navigation-hint {position:fixed;left:16px;bottom:16px;z-index:99999;
              background:#f0fff4;color:#12351f;border:2px solid #39ff14;border-radius:6px;
              padding:10px 14px;font:13px Arial;max-width:85vw;transform-origin:left bottom;
              animation:source-navigation-breathe 2.4s ease-in-out infinite}
            @keyframes source-navigation-breathe {
              0%,100% {transform:scale(1);box-shadow:0 0 5px #39ff1488,0 0 12px #22c55e44}
              50% {transform:scale(.97);box-shadow:0 0 10px #39ff14cc,0 0 24px #39ff1488,0 0 0 5px #39ff1426}
            }
            @media (prefers-reduced-motion:reduce) {#source-navigation-hint {animation:none}}
          `;
          document.head.append(style);
        }
        document.body.append(notice);
      }
      notice.textContent = '请在 IDEA 的 Tools → Open Class Diagram with Source Navigation… 中打开此 HTML，以启用源码导航。';
      clearTimeout(notice.dismiss); notice.dismiss = setTimeout(() => notice.remove(), 7000);
    });
    anchor.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault(); event.stopPropagation(); text.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}));
      }
    });
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    title.textContent = symbolic ? 'IDEA：' + className + (location.methodName ? '#' + location.methodName + '(' + location.parameterTypes.join(', ') + ')' : '') : 'IDEA 本地文件：' + location.file + ':' + location.line;
    text.parentNode.insertBefore(anchor, text); anchor.append(title, text);
  }
  for (const node of svg.querySelectorAll('g.node')) {
    const name = node.id.match(/(?:^|-)classId-(.+)-\d+$/)?.[1];
    const entry = locations[name]; if (!entry) continue;
    const title = [...node.querySelectorAll('text')].find(text => text.textContent.trim() === name);
    if (title) link(title, entry, entry, name);
    const methods = Object.fromEntries(Object.entries(entry.methods || {}).map(([key, value]) => [normalize(key), value]));
    for (const text of node.querySelectorAll('.methods-group text')) {
      const signature = normalize(text.textContent);
      if (methods[signature]) link(text, methods[signature], entry, name + '.' + signature);
    }
  }
}
