// Symbol keys resolve through the same source-map allowlist as the IDEA class viewer.
function linkSequenceSources(svg, index) {
  const symbols = JSON.parse(document.getElementById('source-map').textContent);
  const mapping = JSON.parse(document.getElementById('sequence-links').textContent)[index];
  if (!mapping) return;
  const normalize = value => value.replace(/\s/g, '');
  // Mermaid renders explicit line breaks as separate SVG text fragments.
  const sourceLabel = value => normalize(value.replace(/<\/?br\s*\/?>/gi, ''));
  function decorate(text, links) {
    for (const entry of links || []) {
      const owner = symbols[entry.symbol], location = entry.method ? owner.methods[entry.method] : owner;
      const target = {className: location.className || owner.className,
        ...(entry.method ? {methodName: location.methodName, parameterTypes: location.parameterTypes} : {})};
      const nodes = []; const walker = document.createTreeWalker(text, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) if (!walker.currentNode.parentElement.closest('a,title')) nodes.push(walker.currentNode);
      for (const node of nodes) {
        const at = node.textContent.indexOf(entry.text); if (at < 0) continue;
        const before = node.textContent.slice(0, at), after = node.textContent.slice(at + entry.text.length);
        const link = document.createElementNS('http://www.w3.org/2000/svg', 'a');
        link.classList.add('source-link');link.setAttribute('role','link');link.setAttribute('tabindex','0');
        link.dataset.sourceSymbol=entry.symbol;if(entry.method)link.dataset.sourceMethod=entry.method;
        link.dataset.ideaTarget=JSON.stringify(target);
        const label=target.className+(target.methodName?'#'+target.methodName+'('+target.parameterTypes.join(', ')+')':'');
        link.setAttribute('aria-label',label+'，在 IDEA 中定位源码');
        const title=document.createElementNS('http://www.w3.org/2000/svg','title');title.textContent='IDEA：'+label;
        link.append(title,document.createTextNode(entry.text));
        link.addEventListener('click',event=>{event.preventDefault();if(document.documentElement.dataset.ideaBridgeReady==='true')return;
          let hint=document.getElementById('source-navigation-hint');if(!hint){hint=document.createElement('div');hint.id='source-navigation-hint';hint.setAttribute('role','status');hint.style.cssText='position:fixed;bottom:16px;left:16px;padding:12px;background:#f0fff4;border:2px solid #39ff14;border-radius:6px;z-index:9999;max-width:85vw';document.body.append(hint);}
          hint.textContent='请用支持时序图的 Diagram Source Navigator 在 IDEA 中打开此 HTML。';});
        link.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();link.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));}});
        node.replaceWith(document.createTextNode(before),link,document.createTextNode(after));
        break;
      }
    }
  }
  for (const text of svg.querySelectorAll('text.actor')) {
    const actor = text.parentElement;
    const id = actor.getAttribute('name') ||
      actor.querySelector(':scope > rect.actor[name]')?.getAttribute('name') ||
      actor.getAttribute('data-id');
    const matches = id ? [mapping.participants[id]] : Object.values(mapping.participants)
      .filter(item => sourceLabel(item.label) === normalize(text.textContent));
    if (matches.length === 1 && matches[0]) decorate(text, matches[0].links);
  }
  const labels = Array.from(svg.querySelectorAll('.messageText'));
  const raw = labels.map(text => normalize(text.textContent));
  let cursor = 0;
  for (const item of mapping.messages) {
    const expected = sourceLabel(item.label.replace(/^\s*(?:no)?wrap:\s*/, ''));
    let offset = 0;
    let end = cursor;
    while (end < raw.length && offset < expected.length) {
      let fragment = raw[end++];
      // Preserve source hyphens and skip a hyphen added by automatic wrapping.
      if (!expected.startsWith(fragment, offset) && fragment.endsWith('-')) fragment = fragment.slice(0, -1);
      if (!expected.startsWith(fragment, offset)) break;
      offset += fragment.length;
    }
    if (offset !== expected.length) {
      svg.dataset.sourceLinkError = 'Message grouping differs from mapping';
      return;
    }
    const fragments = labels.slice(cursor, end);
    for (const entry of item.links || []) {
      const fragment = fragments.find(text => text.textContent.includes(entry.text));
      if (fragment) decorate(fragment, [entry]);
      else svg.dataset.sourceLinkError = 'Method name split by wrapping: ' + entry.text;
    }
    cursor = end;
  }
}
