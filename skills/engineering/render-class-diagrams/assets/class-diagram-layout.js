// Align Mermaid's existing vertical layers without changing class membership or edges.
function alignClassLevels(svg) {
  const nodes = [...svg.querySelectorAll('g.node')].map(node => {
    const matrix = node.transform.baseVal.consolidate().matrix;
    const box = node.getBBox();
    return {
      node,
      x: matrix.e,
      y: matrix.f,
      left: matrix.e + box.x,
      right: matrix.e + box.x + box.width,
      top: matrix.f + box.y,
      bottom: matrix.f + box.y + box.height,
      isClass: node.id.includes('-classId-'),
      dy: 0
    };
  });

  // Mermaid leaves a vertical gap between ranks; overlapping class spans share a rank.
  const levels = [];
  for (const node of nodes.filter(node => node.isClass).sort((a, b) => a.top - b.top)) {
    let level = levels[levels.length - 1];
    if (!level || node.top >= level.bottom) {
      level = { top: node.top, bottom: node.bottom, nodes: [] };
      levels.push(level);
    }
    level.bottom = Math.max(level.bottom, node.bottom);
    level.nodes.push(node);
  }
  levels.forEach((level, index) => {
    for (const node of level.nodes) {
      node.dy = level.top - node.top;
      node.node.dataset.layoutLevel = index;
    }
  });

  function endpointNode(point) {
    let closest, distance = Infinity;
    for (const node of nodes) {
      const dx = Math.max(node.left - point.x, 0, point.x - node.right);
      const dy = Math.max(node.top - point.y, 0, point.y - node.bottom);
      const candidate = dx * dx + dy * dy;
      if (candidate < distance) { closest = node; distance = candidate; }
    }
    return distance < 4 ? closest : null;
  }

  const edges = [...svg.querySelectorAll('path.relation')].map(path => {
    const points = JSON.parse(atob(path.dataset.points));
    return { path, points, source: endpointNode(points[0]), target: endpointNode(points[points.length - 1]) };
  });
  // Keep responsibility notes in their original position relative to their class.
  for (const edge of edges) {
    if (edge.source && edge.target) {
      if (!edge.source.isClass && edge.target.isClass) edge.source.dy = edge.target.dy;
      if (edge.source.isClass && !edge.target.isClass) edge.target.dy = edge.source.dy;
    }
  }
  for (const node of nodes) {
    if (node.dy) node.node.setAttribute('transform', `translate(${node.x},${node.y + node.dy})`);
  }
  function borderPoint(point, node) {
    if (!node) return { ...point };
    const result = { x: Math.max(node.left, Math.min(node.right, point.x)), y: point.y + node.dy };
    const sides = [
      { distance: Math.abs(point.y - node.top), y: node.top + node.dy },
      { distance: Math.abs(point.y - node.bottom), y: node.bottom + node.dy },
      { distance: Math.abs(point.x - node.left), x: node.left },
      { distance: Math.abs(point.x - node.right), x: node.right }
    ].sort((a, b) => a.distance - b.distance);
    if ('x' in sides[0]) result.x = sides[0].x;
    else result.y = sides[0].y;
    return result;
  }
  for (const { path, points, source, target } of edges) {
    const route = points.map(point => ({ ...point }));
    route[0] = borderPoint(points[0], source);
    route[route.length - 1] = borderPoint(points[points.length - 1], target);
    // Nearly vertical corridors need one straight spine, not a tiny sideways jog.
    const xs = route.map(point => point.x);
    const spine = (route[0].x + route[route.length - 1].x) / 2;
    if (Math.max(...xs) - Math.min(...xs) < 12 &&
        source && target && spine > source.left && spine < source.right && spine > target.left && spine < target.right) {
      route.forEach(point => { point.x = spine; });
    }
    const orthogonal = [route[0]];
    for (let i = 1; i < route.length; i++) {
      const previous = orthogonal[orthogonal.length - 1], point = route[i];
      if (Math.abs(point.x - previous.x) > 0.01 && Math.abs(point.y - previous.y) > 0.01) {
        orthogonal.push(i === route.length - 1 ? { x: point.x, y: previous.y } : { x: previous.x, y: point.y });
      }
      orthogonal.push(point);
    }
    const d = orthogonal.map((point, i) => `${i ? 'L' : 'M'}${point.x},${point.y}`).join('');
    path.setAttribute('d', roundedOrthogonalRelationPath(d));
    // Mermaid's margin markers intentionally stop short. Anchor the visible tip,
    // rather than the back of the marker, exactly on the class-box border.
    for (const end of ['start', 'end']) {
      const id = path.getAttribute('marker-' + end)?.match(/#([^)]*)/)[1];
      const marker = id && svg.querySelector(`[id="${id}"]`);
      const shape = marker?.querySelector('path,polygon');
      if (!shape) continue;
      const box = shape.getBBox();
      marker.setAttribute('refX', end === 'start' ? box.x : box.x + box.width);
      marker.setAttribute('refY', box.y + box.height / 2);
      marker.dataset.borderAttached = 'true';
      // Hollow UML markers must occlude the spine behind their interior.
      // Dependency/composition markers keep their original solid appearance.
      if (marker.classList.contains('extension') || marker.classList.contains('aggregation')) {
        shape.style.setProperty('fill', '#ffffff', 'important');
      }
    }
  }
  svg.dataset.levelAligned = 'true';
}

// Keep horizontal/vertical trunks and soften bends with small rounded corners.
// Unsupported or genuinely diagonal routes retain Mermaid's path rather than being
// blindly rerouted through neighboring boxes or detached from their arrowheads.
function roundedOrthogonalRelationPath(d) {
  const commands = [...d.matchAll(/([MLQACHVSTZ])([^MLQACHVSTZ]*)/g)];
  const points = [];
  for (const [, command, body] of commands) {
    const values = (body.match(/[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:e[-+]?\d+)?/gi) || []).map(Number);
    if ((command === 'M' || command === 'L') && values.length === 2) {
      points.push({ x: values[0], y: values[1] });
    } else if (command === 'Q' && values.length === 4) {
      points.push({ x: values[0], y: values[1] }, { x: values[2], y: values[3] });
    } else return d;
  }
  if (!points.length) return d;
  const route = [points[0]];
  for (const point of points.slice(1)) {
    const previous = route[route.length - 1];
    const dx = Math.abs(point.x - previous.x), dy = Math.abs(point.y - previous.y);
    if (dx > 0.01 && dy > 0.01) return d;
    if (dx < 0.0001 && dy < 0.0001) continue;
    route.push(point);
  }
  // Remove intermediate collinear vertices before applying a bounded 6px radius.
  const vertices = [];
  for (const point of route) {
    while (vertices.length > 1) {
      const a = vertices[vertices.length - 2], b = vertices[vertices.length - 1];
      const sameX = Math.abs(a.x - b.x) < 0.01 && Math.abs(b.x - point.x) < 0.01;
      const sameY = Math.abs(a.y - b.y) < 0.01 && Math.abs(b.y - point.y) < 0.01;
      const forward = (b.x - a.x) * (point.x - b.x) + (b.y - a.y) * (point.y - b.y) >= 0;
      if (!(sameX || sameY) || !forward) break;
      vertices.pop();
    }
    vertices.push(point);
  }
  let result = `M${vertices[0].x},${vertices[0].y}`;
  for (let i = 1; i < vertices.length - 1; i++) {
    const a = vertices[i - 1], b = vertices[i], c = vertices[i + 1];
    const incoming = Math.hypot(b.x - a.x, b.y - a.y), outgoing = Math.hypot(c.x - b.x, c.y - b.y);
    const turn = (b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x);
    if (Math.abs(turn) < 0.01) { result += `L${b.x},${b.y}`; continue; }
    const radius = Math.min(6, incoming / 2, outgoing / 2);
    const entry = { x: b.x - (b.x - a.x) / incoming * radius, y: b.y - (b.y - a.y) / incoming * radius };
    const exit = { x: b.x + (c.x - b.x) / outgoing * radius, y: b.y + (c.y - b.y) / outgoing * radius };
    result += `L${entry.x},${entry.y}Q${b.x},${b.y} ${exit.x},${exit.y}`;
  }
  if (vertices.length > 1) { const end = vertices[vertices.length - 1]; result += `L${end.x},${end.y}`; }
  return result;
}
