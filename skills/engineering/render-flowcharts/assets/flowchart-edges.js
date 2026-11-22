// Preserve Dagre's lanes while shortening clear side exits and rounding bends.
function straightenFlowchartEdges(svg, direction, source) {
  const horizontal = direction === 'LR' || direction === 'RL';
  const labels = new Map(Array.from(svg.querySelectorAll('.edgeLabel [data-id]'),
    label => [label.dataset.id, label.closest('.edgeLabel')]));
  const nodes = Array.from(svg.querySelectorAll('g.node'));
  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

  function boundsInPath(element, path) {
    const box = element.getBBox();
    const matrix = path.getCTM().inverse().multiply(element.getCTM());
    return [
      new DOMPoint(box.x, box.y).matrixTransform(matrix),
      new DOMPoint(box.x + box.width, box.y + box.height).matrixTransform(matrix),
    ];
  }

  function within(point, [a, b]) {
    return point.x >= a.x - 1 && point.x <= b.x + 1 && point.y >= a.y - 1 && point.y <= b.y + 1;
  }

  function crossesNode(start, end, path) {
    return nodes.some(node => {
      const bounds = boundsInPath(node, path);
      const [a, b] = bounds;
      // Both ports can already sit inside the bounding box of a rounded shape.
      if (within(start, bounds) || within(end, bounds)) return false;
      let near = 0;
      let far = 1;
      for (const axis of ['x', 'y']) {
        const delta = end[axis] - start[axis];
        if (!delta) {
          if (start[axis] <= a[axis] || start[axis] >= b[axis]) return false;
          continue;
        }
        const enter = (a[axis] - start[axis]) / delta;
        const leave = (b[axis] - start[axis]) / delta;
        near = Math.max(near, Math.min(enter, leave));
        far = Math.min(far, Math.max(enter, leave));
      }
      return near < far;
    });
  }

  function sideExit(points, path) {
    if (horizontal || points.length < 4) return points;
    const [start, lane, next] = points;
    if (Math.abs(lane.x - next.x) > .001) return points;
    const shape = nodes.map(node => node.querySelector(':scope > .label-container')).find(shape => {
      if (!shape?.isPointInFill) return false;
      const bounds = boundsInPath(shape, path);
      if (!within(start, bounds)) return false;
      const transform = shape.getCTM().inverse().multiply(path.getCTM());
      return shape.isPointInFill(new DOMPoint(start.x, start.y).matrixTransform(transform))
        || bounds.some(edge => Math.abs(start.x - edge.x) < .01 || Math.abs(start.y - edge.y) < .01);
    });
    if (!shape) return points;

    const [a, b] = boundsInPath(shape, path);
    const side = lane.x > b.x + 12 ? b.x : lane.x < a.x - 12 ? a.x : null;
    if (side === null) return points;
    const port = { x: side, y: (a.y + b.y) / 2 };
    const insideX = side + (side === a.x ? 1 : -1);
    const toShape = shape.getCTM().inverse().multiply(path.getCTM());
    if (!shape.isPointInFill(new DOMPoint(insideX, port.y).matrixTransform(toShape))) return points;

    const bend = { x: lane.x, y: port.y };
    if (crossesNode(port, bend, path) || crossesNode(bend, next, path)) return points;
    return [port, bend, ...points.slice(2)];
  }

  function orthogonalPoints(points) {
    const result = [points[0]];
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1];
      const b = points[i];
      if (a.x !== b.x && a.y !== b.y) {
        if (horizontal) {
          const x = (a.x + b.x) / 2;
          result.push({ x, y: a.y }, { x, y: b.y });
        } else {
          const y = (a.y + b.y) / 2;
          result.push({ x: a.x, y }, { x: b.x, y });
        }
      }
      result.push(b);
    }
    return result.filter((p, i) => !i || distance(result[i - 1], p) > 0.001)
      .filter((p, i, sequence) => {
        const before = sequence[i - 1];
        const after = sequence[i + 1];
        if (!before || !after) return true;
        const between = (a, b, c) => b >= Math.min(a, c) && b <= Math.max(a, c);
        const redundantX = before.x === p.x && p.x === after.x && between(before.y, p.y, after.y);
        const redundantY = before.y === p.y && p.y === after.y && between(before.x, p.x, after.x);
        return !redundantX && !redundantY;
      });
  }

  function inset(port, next, gap) {
    const length = distance(port, next);
    if (!length) return port;
    const ratio = Math.min(gap / length, .9);
    return { x: port.x + (next.x - port.x) * ratio, y: port.y + (next.y - port.y) * ratio };
  }

  function roundedPath(points) {
    const pair = ({ x, y }) => x + ',' + y;
    let result = 'M' + pair(points[0]);
    for (let i = 1; i < points.length - 1; i++) {
      const [before, corner, after] = points.slice(i - 1, i + 2);
      const rightAngle = (before.x === corner.x && corner.y === after.y)
        || (before.y === corner.y && corner.x === after.x);
      const radius = Math.min(12, distance(before, corner) * .45, distance(corner, after) * .45);
      if (!rightAngle || radius < 1) {
        result += 'L' + pair(corner);
        continue;
      }
      result += 'L' + pair(inset(corner, before, radius))
        + 'Q' + pair(corner) + ' ' + pair(inset(corner, after, radius));
    }
    return result + 'L' + pair(points.at(-1));
  }

  // A diagram may specify aligned columns and precise ports where automatic
  // placement leaves a prominent path misaligned.
  const spec = source.match(/^\s*%%\s*aligned-layout:\s*(\{[^\n]+\})/m);
  function applyAlignedLayout(layout) {
    const paths = Array.from(svg.querySelectorAll('path.flowchart-link[data-points]'));
    if (!paths.length) return false;
    const originalPositions = new Map(nodes.map(node => [node, node.getAttribute('transform')]));
    const nodeById = new Map(nodes.map(node => [node.id.match(/-flowchart-(.+)-\d+$/)?.[1], node]));
    const originalShapes = new Map();
    for (const [id, ratio] of Object.entries(layout.decisionHeight || {})) {
      const shape = nodeById.get(id)?.querySelector(':scope > polygon.label-container');
      if (!shape || !Number.isFinite(ratio) || ratio < .45 || ratio >= 1) continue;
      const box = shape.getBBox();
      const center = box.y + box.height / 2;
      const transform = shape.getAttribute('transform');
      originalShapes.set(shape, transform);
      shape.setAttribute('transform', (transform || '') + ' translate(0,' + center + ') scale(1,' + ratio + ') translate(0,' + -center + ')');
    }
    for (const [id, x] of Object.entries(layout.columns)) {
      const node = nodeById.get(id);
      if (!node || !paths.length) continue;
      const shape = node.querySelector(':scope > .label-container') || node;
      const [a, b] = boundsInPath(shape, paths[0]);
      const transform = node.transform.baseVal.getItem(0);
      const row = layout.rows?.[id];
      const y = Number.isFinite(row) ? transform.matrix.f + row - (a.y + b.y) / 2 : transform.matrix.f;
      transform.setTranslate(transform.matrix.e + x - (a.x + b.x) / 2, y);
    }
    for (const [id, reference] of Object.entries(layout.alignTop || {})) {
      const node = nodeById.get(id);
      const target = nodeById.get(reference);
      if (!node || !target || !paths.length) continue;
      const top = item => boundsInPath(item.querySelector(':scope > .label-container') || item, paths[0])[0].y;
      const transform = node.transform.baseVal.getItem(0);
      transform.setTranslate(transform.matrix.e, transform.matrix.f + top(target) - top(node));
    }
    const boxes = nodes.map(node => boundsInPath(node, paths[0]));
    const clearance = 8;
    const collision = boxes.some(([a, b], i) => boxes.slice(i + 1).some(([c, d]) =>
      b.x + clearance > c.x && d.x + clearance > a.x &&
      b.y + clearance > c.y && d.y + clearance > a.y));
    if (collision) {
      for (const [node, transform] of [...originalPositions, ...originalShapes]) {
        if (transform === null) node.removeAttribute('transform');
        else node.setAttribute('transform', transform);
      }
      return false;
    }

    for (const [from, to, fromSide, toSide, fromOffset = 0, toOffset = 0, lane] of layout.edges) {
      const edge = paths.find(path => path.dataset.id === 'L_' + from + '_' + to + '_0');
      if (!edge) continue;
      function port(id, side, offset) {
        const node = nodeById.get(id);
        const shape = node.querySelector(':scope > .label-container') || node;
        const [a, b] = boundsInPath(shape, edge);
        return side === 'right' || side === 'left'
          ? {x: side === 'right' ? b.x : a.x, y: (a.y + b.y) / 2 + offset}
          : {x: (a.x + b.x) / 2 + offset, y: side === 'top' ? a.y : b.y};
      }
      const start = port(from, fromSide, fromOffset);
      const end = port(to, toSide, toOffset);
      let route = [start, end];
      if (Number.isFinite(lane)) {
        route = [start, {x:lane,y:start.y}, {x:lane,y:end.y}, end];
      } else if (fromSide === 'right') {
        route = [start, {x:end.x,y:start.y}, end];
      }
      route[route.length - 1] = inset(end, route.at(-2), 4);
      edge.setAttribute('d', roundedPath(route));
      const label = labels.get(edge.dataset.id);
      if (label?.hasAttribute('transform')) {
        const x = Number.isFinite(lane) ? lane : fromSide === 'right' ? end.x : (start.x + end.x) / 2;
        const y = (start.y + end.y) / 2;
        label.setAttribute('transform', 'translate(' + x + ', ' + y + ')');
      }
    }
    const bounds = svg.querySelector('g').getBBox();
    svg.setAttribute('viewBox', [bounds.x-8,bounds.y-8,bounds.width+16,bounds.height+16].join(' '));
    return true;
  }

  if (spec && applyAlignedLayout(JSON.parse(spec[1]))) return;
  for (const path of svg.querySelectorAll('path.flowchart-link[data-points]')) {
    // Explicit curve choices can produce paths with commands other than M/L.
    if (!/^[ML0-9.,+eE\s-]+$/.test(path.getAttribute('d'))) continue;
    const points = JSON.parse(atob(path.getAttribute('data-points')));
    if (points.length < 2) continue;
    const start = points[0];
    const end = points.at(-1);
    const length = path.getTotalLength();
    if (!length || distance(start, end) < .001) continue;
    const straight = points.length <= 3 && !crossesNode(start, end, path);
    const route = straight ? [start, end] : orthogonalPoints(sideExit(points, path));
    if (route.length < 2) continue;
    route[0] = inset(route[0], route[1], distance(start, path.getPointAtLength(0)));
    route[route.length - 1] = inset(end, route.at(-2), distance(end, path.getPointAtLength(length)));
    path.setAttribute('d', roundedPath(route));

    const label = labels.get(path.dataset.id);
    if (straight && label?.hasAttribute('transform')) {
      const labelX = start.x + .65 * (end.x - start.x);
      const labelY = start.y + .65 * (end.y - start.y);
      label.setAttribute('transform', 'translate(' + labelX + ', ' + labelY + ')');
    }
  }
}
