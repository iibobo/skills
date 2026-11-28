function isFlowchartDecision(shape) {
  if (!shape?.matches('polygon') || shape.points.numberOfItems !== 4) return false;
  const close = (a, b) => Math.abs(a - b) < .01;
  const {x, y, width, height} = shape.getBBox();
  return Array.from(shape.points).every(point =>
    (close(point.x, x + width / 2) && (close(point.y, y) || close(point.y, y + height)))
    || (close(point.y, y + height / 2) && (close(point.x, x) || close(point.x, x + width))));
}


// Reuse Mermaid's node layout and routing lanes for orthogonal connectors.
function straightenFlowchartEdges(svg, direction, source, adjustLayout = true) {
  const root = svg.querySelector('g.root') || svg.querySelector('g');
  const paths = Array.from(svg.querySelectorAll('path.flowchart-link[data-points]'));
  if (!root) return;
  const nodes = Array.from(svg.querySelectorAll('g.node'));
  const sides = ['top', 'right', 'bottom', 'left'];
  const normals = {top: [0, -1], right: [1, 0], bottom: [0, 1], left: [-1, 0]};
  const horizontal = direction === 'LR' || direction === 'RL';
  const north = direction === 'BT' ? 'bottom' : 'top';
  const clearance = 5;
  const stem = 12;
  const epsilon = .01;

  const shift = (point, [dx, dy], amount) => ({x: point.x + dx * amount, y: point.y + dy * amount});
  const distance = (a, b) => Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
  const middle = (a, b) => (a + b) / 2;
  const close = (a, b) => Math.abs(a - b) < epsilon;
  const shapeOf = node => node.querySelector(':scope > .label-container') || node;
  const nodeId = node => node.id.match(/-flowchart-(.+)-\d+$/)?.[1];
  const svgElement = (name, attributes = {}) => {
    const element = document.createElementNS(svg.namespaceURI, name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    return element;
  };

  function transformPoint(point, matrix) {
    return new DOMPoint(point.x, point.y).matrixTransform(matrix);
  }

  function boundsInPath(element, frame) {
    const {x, y, width, height} = element.getBBox();
    const matrix = frame.getCTM().inverse().multiply(element.getCTM());
    return [transformPoint({x, y}, matrix), transformPoint({x: x + width, y: y + height}, matrix)];
  }

  function boxOf(element) {
    const [a, b] = boundsInPath(element, root);
    return {a, b, center: {x: middle(a.x, b.x), y: middle(a.y, b.y)}};
  }

  function portOf(node, side, offset = 0) {
    const {a, b, center, shape} = node;
    const [dx, dy] = normals[side];
    const axis = dx ? 'x' : 'y';
    const point = shift(center, [Math.abs(dy), Math.abs(dx)], offset);
    const edge = dx + dy < 0 ? a[axis] : b[axis];
    point[axis] = edge;
    if (!shape.isPointInFill || node.decision) return point;
    const matrix = shape.getCTM().inverse().multiply(root.getCTM());
    const inShape = p => shape.isPointInFill(transformPoint(p, matrix));
    const inside = {...point, [axis]: center[axis]};
    if (!inShape(inside) || inShape(shift(point, normals[side], -.05))) return point;
    // Sloped and curved shapes can meet the centerline inside their bounding box.
    let inner = center[axis];
    let outer = edge;
    while (Math.abs(inner - outer) > .02) {
      const mid = middle(inner, outer);
      if (inShape({...point, [axis]: mid})) inner = mid;
      else outer = mid;
    }
    return {...point, [axis]: inner};
  }

  function boxesOverlap(left, right, pad = 0) {
    return left.a.x < right.b.x + pad && left.b.x > right.a.x - pad
      && left.a.y < right.b.y + pad && left.b.y > right.a.y - pad;
  }

  function isInside(point, {a, b}, pad = 0) {
    return point.x > a.x - pad && point.x < b.x + pad && point.y > a.y - pad && point.y < b.y + pad;
  }

  function segmentTouches(a, b, box, pad = 0) {
    const axis = close(a.y, b.y) ? 'x' : 'y';
    const fixed = axis === 'x' ? 'y' : 'x';
    return a[fixed] > box.a[fixed] - pad && a[fixed] < box.b[fixed] + pad
      && Math.max(a[axis], b[axis]) > box.a[axis] - pad && Math.min(a[axis], b[axis]) < box.b[axis] + pad;
  }

  function simplify(points) {
    const result = [];
    for (const point of points) {
      const last = result.at(-1);
      if (last && distance(last, point) < epsilon) continue;
      const before = result.at(-2);
      if (before && close(distance(before, point), distance(before, last) + distance(last, point))
          && ((close(before.x, last.x) && close(last.x, point.x)) || (close(before.y, last.y) && close(last.y, point.y)))) {
        result.pop();
      }
      result.push(point);
    }
    return result;
  }

  function orthogonalPoints(points, useHorizontal) {
    const result = [points[0]];
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1];
      const b = points[i];
      if (!close(a.x, b.x) && !close(a.y, b.y)) {
        if (useHorizontal) {
          const x = middle(a.x, b.x);
          result.push({x, y: a.y}, {x, y: b.y});
        } else {
          const y = middle(a.y, b.y);
          result.push({x: a.x, y}, {x: b.x, y});
        }
      }
      result.push(b);
    }
    return simplify(result);
  }

  function segments(points) {
    return points.slice(1).map((b, i) => {
      const a = points[i];
      const axis = close(a.y, b.y) ? 'x' : 'y';
      const fixed = axis === 'x' ? 'y' : 'x';
      return {a, b, axis, fixed, at: a[fixed], min: Math.min(a[axis], b[axis]), max: Math.max(a[axis], b[axis])};
    });
  }

  function crossing(a, b, margin) {
    if (a.axis === b.axis || b.at <= a.min + margin || b.at >= a.max - margin
        || a.at <= b.min + margin || a.at >= b.max - margin) return null;
    return {[a.axis]: b.at, [b.axis]: a.at};
  }

  function endInset(port, next, gap) {
    const ratio = Math.min(gap / distance(port, next), .9);
    return {x: port.x + (next.x - port.x) * ratio, y: port.y + (next.y - port.y) * ratio};
  }

  const spec = source.match(/^\s*%%\s*aligned-layout:\s*(\{[^\n]+\})/m);
  function applyAlignedLayout(layout) {
    const originalPositions = new Map(nodes.map(node => [node, node.getAttribute('transform')]));
    const nodeById = new Map(nodes.map(node => [nodeId(node), node]));
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
    for (const [id, x] of Object.entries(layout.columns || {})) {
      const node = nodeById.get(id);
      if (!node || !Number.isFinite(x)) continue;
      const shape = shapeOf(node);
      const [a, b] = boundsInPath(shape, root);
      const transform = node.transform.baseVal.getItem(0);
      const row = layout.rows?.[id];
      const y = Number.isFinite(row) ? transform.matrix.f + row - (a.y + b.y) / 2 : transform.matrix.f;
      transform.setTranslate(transform.matrix.e + x - (a.x + b.x) / 2, y);
    }
    for (const [id, reference] of Object.entries(layout.alignTop || {})) {
      const node = nodeById.get(id);
      const target = nodeById.get(reference);
      if (!node || !target) continue;
      const top = item => boundsInPath(shapeOf(item), root)[0].y;
      const transform = node.transform.baseVal.getItem(0);
      transform.setTranslate(transform.matrix.e, transform.matrix.f + top(target) - top(node));
    }
    const boxes = nodes.map(node => boundsInPath(node, root));
    const clearance = 8;
    function restore() {
      for (const [node, transform] of [...originalPositions, ...originalShapes]) {
        if (transform === null) node.removeAttribute('transform');
        else node.setAttribute('transform', transform);
      }
    }
    const collision = boxes.some(([a, b], i) => boxes.slice(i + 1).some(([c, d]) =>
      b.x + clearance > c.x && d.x + clearance > a.x &&
      b.y + clearance > c.y && d.y + clearance > a.y));
    if (collision) {
      restore();
      return null;
    }
    return restore;
  }

  // Resolve links before moving nodes so custom edge IDs and parallel links retain their endpoints.
  const originalNodes = nodes.map(node => ({node, ...boxOf(shapeOf(node))}));
  function nodeAt(point) {
    return originalNodes.filter(node => isInside(point, node, 1)).sort((a, b) =>
      distance(point, a.center) - distance(point, b.center))[0]?.node;
  }

  const labels = new Map(Array.from(svg.querySelectorAll('.edgeLabel [data-id]'),
    label => [label.dataset.id, label.closest('.edgeLabel')]));
  const edges = [];
  for (const path of paths) {
    // Source-defined curves keep Mermaid's geometry.
    if (!/^[ML0-9.,+eE\s-]+$/.test(path.getAttribute('d'))) continue;
    const points = JSON.parse(atob(path.dataset.points));
    if (points.length < 2) continue;
    const matrix = root.getCTM().inverse().multiply(path.getCTM());
    const guide = points.map(point => transformPoint(point, matrix));
    const from = nodeAt(guide[0]);
    const to = nodeAt(guide.at(-1));
    const length = path.getTotalLength();
    if (!from || !to || !length) continue;
    const gap = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    edges.push({path, guide, from, to, toPath: matrix.inverse(),
      startGap: gap(points[0], path.getPointAtLength(0)), endGap: gap(points.at(-1), path.getPointAtLength(length)),
      label: labels.get(path.dataset.id), marker: path.getAttribute('marker-end'),
      stroke: [path.getAttribute('class'), path.getAttribute('style')].join('|')});
  }

  function compactDecisions() {
    const changed = new Map();
    const bounds = new Map(nodes.map(node => [node, boxOf(shapeOf(node))]));
    const clusters = Array.from(svg.querySelectorAll('.cluster > rect'), boxOf);
    for (const node of nodes) {
      const shape = shapeOf(node);
      const label = node.querySelector(':scope > .label');
      if (!isFlowchartDecision(shape) || !label) continue;
      const original = shape.getBBox();
      const center = {x: original.x + original.width / 2, y: original.y + original.height / 2};
      const rows = Array.from(label.querySelectorAll('tspan.row'));
      const text = (rows.length ? rows : [label]).map(row => {
        const [a, b] = boundsInPath(row, shape);
        return {width: 2 * (Math.max(center.x - a.x, b.x - center.x) + 7),
          height: 2 * (Math.max(center.y - a.y, b.y - center.y) + 4)};
      });
      // A diamond tapers vertically. Size it for the padded corners of each text row.
      const preferredHeight = Math.max(96, original.width * .55);
      const widthForText = Math.max(...text.map(row => row.width / Math.max(.01, 1 - row.height / preferredHeight)));
      let width = Math.min(original.width + 30, Math.max(original.width, widthForText));
      const heightFor = width => Math.max(preferredHeight, ...text.map(row =>
        row.height / Math.max(.01, 1 - row.width / width)));
      let height = heightFor(width);
      const frame = root.getCTM().inverse().multiply(shape.getCTM());
      function resizedBox() {
        return {
          a: transformPoint({x: center.x - width / 2, y: center.y - height / 2}, frame),
          b: transformPoint({x: center.x + width / 2, y: center.y + height / 2}, frame),
        };
      }
      if (width > original.width) {
        const next = resizedBox();
        const collision = [...bounds].some(([other, box]) => other !== node && boxesOverlap(next, box, clearance));
        const crossesGroup = clusters.some(box => boxesOverlap(next, box)
          && (!boxesOverlap(bounds.get(node), box) || next.a.x < box.a.x + clearance || next.b.x > box.b.x - clearance));
        if (collision || crossesGroup) {
          width = original.width;
          height = heightFor(width);
        }
      }
      if (height >= original.height - 1 || text.some(row => row.width >= width)) continue;
      changed.set(node, {shape, points: shape.getAttribute('points')});
      const scaleX = width / original.width;
      const scaleY = height / original.height;
      shape.setAttribute('points', Array.from(shape.points, point =>
        (center.x + (point.x - center.x) * scaleX) + ',' + (center.y + (point.y - center.y) * scaleY)).join(' '));
      bounds.set(node, resizedBox());
    }
    return changed;
  }

  const automaticLayout = adjustLayout && !spec && edges.length === paths.length;
  const compacted = automaticLayout ? compactDecisions() : new Map();
  if (!paths.length && !compacted.size) return;
  const layout = spec && edges.length === paths.length ? JSON.parse(spec[1]) : null;
  const restoreLayout = layout && applyAlignedLayout(layout);
  const manual = restoreLayout ? layout.edges || [] : [];
  const geometry = new Map(nodes.map(node => {
    const shape = shapeOf(node);
    return [node, {...boxOf(shape), node, shape, decision: isFlowchartDecision(shape)}];
  }));
  const obstacles = [...geometry.values(), ...Array.from(svg.querySelectorAll('.cluster-label'), boxOf)];
  const used = [];

  function preferredSide(node, anchor) {
    const score = side => distance(portOf(node, side), anchor);
    return sides.reduce((best, side) => score(side) < score(best) - epsilon ? side : best);
  }

  const outgoing = new Map(nodes.map(node => [node, []]));
  for (const edge of edges) outgoing.get(edge.from).push(edge);
  const isAffirmative = edge => /^是(?:$|[：:、，,\s])/.test(edge.label?.textContent.trim() || '');
  const mainline = new Set();
  const exits = new Map();
  function assignSideExits(node) {
    if (!node.decision) return;
    const allBranches = outgoing.get(node.node);
    const branches = allBranches.filter(edge => !mainline.has(edge));
    const targetX = edge => geometry.get(edge.to).center.x;
    const laneX = edge => edge.guide.find(point => Math.abs(point.x - node.center.x) > (node.b.x - node.a.x) / 2 + 8)?.x
      ?? targetX(edge);
    branches.sort((a, b) => laneX(a) - laneX(b));
    branches.forEach((edge, i) => {
      const x = branches.length === 1 && allBranches.length > 1 ? targetX(edge) : laneX(edge);
      const side = branches.length === 2 ? ['left', 'right'][i] : x < node.center.x ? 'left' : 'right';
      exits.set(edge, side);
    });
  }

  function safe(a, b, ignored) {
    return !obstacles.some(box => (!ignored || box.node !== ignored) && segmentTouches(a, b, box, clearance));
  }

  function alignBranchColumns() {
    const clusters = Array.from(svg.querySelectorAll('.cluster > rect'), boxOf);
    const originalX = new Map(originalNodes.map(({node, center}) => [node, center.x]));
    const incoming = new Map();
    for (const {to} of edges) incoming.set(to, (incoming.get(to) || 0) + 1);
    const aligned = [];
    const originalPositions = new Map();
    const locked = new Set();
    const forward = -normals[north][1];

    function align(edge, side, maxShift, minimumRun) {
      const from = geometry.get(edge.from);
      const target = geometry.get(edge.to);
      const start = portOf(from, side);
      const corner = shift(start, normals[side], Math.max(stem, edge.startGap + 8));
      const entry = portOf(target, north);
      const dx = corner.x - entry.x;
      if (Math.abs(dx) > maxShift || (entry.y - corner.y) * forward <= 0 || !safe(start, corner, edge.from)) return false;
      if (Math.abs(dx) >= epsilon && locked.has(target)) return false;

      const column = new Set([target]);
      for (let last = target; !last.decision;) {
        const destinations = outgoing.get(last.node);
        if (destinations.length !== 1) break;
        const next = geometry.get(destinations[0].to);
        if (incoming.get(next.node) !== 1 || locked.has(next)
            || (next.center.y - last.center.y) * forward <= 0
            || Math.abs(next.center.x - target.center.x) > 1) break;
        last = next;
        column.add(last);
      }
      const fixed = obstacles.filter(box => !column.has(box));
      const bounds = [...column].map(item => boxOf(item.node));
      const offsets = new Set([0]);
      if (!locked.has(target)) {
        // Try the nearest clear row above or below shapes that block the new column.
        for (const box of bounds) {
          for (const other of fixed) {
            if (box.a.x + dx >= other.b.x + clearance || box.b.x + dx <= other.a.x - clearance) continue;
            offsets.add(other.a.y - box.b.y - clearance - 3);
            offsets.add(other.b.y - box.a.y + clearance + 3);
          }
        }
      }
      const maxRowShift = side === 'bottom' ? 96 : 48;
      const candidates = [...offsets].filter(dy => Math.abs(dy) <= maxRowShift).sort((a, b) => Math.abs(a) - Math.abs(b));
      for (const dy of candidates) {
        const end = {x: corner.x, y: entry.y + dy};
        if ((end.y - corner.y) * forward < minimumRun || !safe(corner, end, edge.to)) continue;
        if (bounds.some(original => {
          const shifted = {a: shift(original.a, [dx, dy], 1), b: shift(original.b, [dx, dy], 1)};
          return clusters.some(cluster => boxesOverlap(original, cluster) !== boxesOverlap(shifted, cluster)
            || (boxesOverlap(shifted, cluster) && (shifted.a.x < cluster.a.x + clearance || shifted.b.x > cluster.b.x - clearance
              || shifted.a.y < cluster.a.y + clearance || shifted.b.y > cluster.b.y - clearance)))
            || fixed.some(box => boxesOverlap(shifted, box, clearance))
            || aligned.some(([a, b]) => segmentTouches(a, b, shifted, clearance));
        })) continue;
        if (dy && edges.some(({from, to}) => {
          const before = geometry.get(from);
          const after = geometry.get(to);
          const offset = (Number(column.has(after)) - Number(column.has(before))) * dy;
          const gap = after.center.y - before.center.y;
          return Math.abs(gap) > epsilon && Math.sign(gap) !== Math.sign(gap + offset);
        })) continue;
        if (Math.abs(dx) >= epsilon || Math.abs(dy) >= epsilon) {
          for (const item of column) {
            originalPositions.set(item.node, item.node.getAttribute('transform'));
            const transform = item.node.transform.baseVal.getItem(0);
            const frame = item.node.parentNode.getCTM().inverse().multiply(root.getCTM());
            transform.setTranslate(transform.matrix.e + dx * frame.a + dy * frame.c,
              transform.matrix.f + dx * frame.b + dy * frame.d);
            Object.assign(item, boxOf(item.shape));
            locked.add(item);
          }
        }
        aligned.push([start, corner], [corner, end]);
        return true;
      }
      return false;
    }

    // Place branches in reading order so an adjusted decision can align its own successor.
    const decisions = [...geometry.values()].filter(node => node.decision)
      .sort((a, b) => (a.center.y - b.center.y) * forward);
    for (const from of decisions) {
      const branches = outgoing.get(from.node);
      if (direction !== 'BT') {
        for (const edge of branches.filter(isAffirmative)) {
          const target = geometry.get(edge.to);
          const inlineShape = target.decision || target.shape.matches('rect') || target.shape.querySelector(':scope > rect');
          if (!inlineShape && outgoing.get(target.node).length) continue;
          const maxShift = inlineShape ? Math.max(from.b.x - from.a.x, target.b.x - target.a.x)
            : 30 + Math.abs(from.center.x - originalX.get(from.node));
          if (!align(edge, 'bottom', maxShift, edge.endGap + clearance)) continue;
          mainline.add(edge);
          locked.add(from);
          locked.add(target);
          break;
        }
      }
      assignSideExits(from);
      for (const edge of branches) {
        if (!isAffirmative(edge) && incoming.get(edge.to) === 1 && !locked.has(geometry.get(edge.to))) {
          align(edge, exits.get(edge), 30, stem + edge.endGap + 8);
        }
      }
    }
    return originalPositions;
  }

  // Preserve explicit positions and leave unsupported edges attached to their original nodes.
  const autoPositions = automaticLayout && !horizontal ? alignBranchColumns() : new Map();
  if (!automaticLayout || horizontal) geometry.forEach(assignSideExits);

  function canShareArrow(a, b) {
    return a.to === b.to && a.from !== b.from && a.marker && a.marker === b.marker && a.stroke === b.stroke;
  }

  function sameApproach(a, b) {
    return a.axis === b.axis && close(a.at, b.at) && close(a.b[a.axis], b.b[b.axis])
      && Math.sign(a.b[a.axis] - a.a[a.axis]) === Math.sign(b.b[b.axis] - b.a[b.axis]);
  }

  function chooseRoute(edge) {
    const from = geometry.get(edge.from);
    const to = geometry.get(edge.to);
    const [rawStart, rawEnd] = [edge.guide[0], edge.guide.at(-1)];
    const [, , fromSide, toSide, fromOffset = 0, toOffset = 0, manualLane] = manual.find(([a, b]) =>
      a === nodeId(edge.from) && b === nodeId(edge.to)) || [];
    if (mainline.has(edge) || (!horizontal && from.decision && fromSide === 'bottom' && toSide === 'top' && !toOffset)) {
      const start = portOf(from, 'bottom');
      const end = portOf(to, 'top');
      const pastSource = shift(start, normals.bottom, clearance + 1);
      if (close(start.x, end.x) && end.y > pastSource.y + edge.endGap
          && safe(start, pastSource, edge.from) && safe(pastSource, end, edge.to)) {
        return [start, {...end, x: start.x}];
      }
    }
    const lateralExit = exits.get(edge);
    const decisionExit = ['bottom', 'left', 'right'].includes(fromSide) ? fromSide
      : isAffirmative(edge) ? 'bottom' : lateralExit;
    const preferredExit = from.decision ? decisionExit : fromSide || preferredSide(from, rawStart);
    const preferredEntry = to.decision ? north : toSide || preferredSide(to, rawEnd);
    const exitSides = from.decision ? [...new Set([preferredExit, lateralExit, 'left', 'right'].filter(Boolean))] : sides;
    const entrySides = to.decision ? ['top', 'bottom'] : sides;
    const guide = edge.guide.slice(1, -1);
    const oldLanes = segments(orthogonalPoints(edge.guide, horizontal));
    const xLanes = oldLanes.filter(line => line.axis === 'y').map(line => line.at);
    const yLanes = oldLanes.filter(line => line.axis === 'x').map(line => line.at);
    for (const box of obstacles) {
      xLanes.push(box.a.x - 10, box.b.x + 10);
      yLanes.push(box.a.y - 10, box.b.y + 10);
    }
    let best = null;
    let scoreBest = Infinity;
    const portPenalty = 140;

    function consider(candidate, penalty) {
      const route = simplify(candidate);
      const parts = segments(route);
      if (parts.length === 0 || parts.some((line, i) => line.axis === parts[i - 1]?.axis)) return;
      let score = penalty + 14 * (parts.length - 1);
      for (const [i, line] of parts.entries()) {
        const length = line.max - line.min;
        const approach = i === parts.length - 1;
        score += length;
        if (i > 0 && !approach && length < 18) score += 45;
        if (score >= scoreBest) return;
        for (const other of used) {
          if (approach && other.approach && canShareArrow(edge, other.edge) && sameApproach(line, other)) continue;
          if (other.axis === line.axis && Math.abs(other.at - line.at) < 4) {
            score += Math.max(0, Math.min(line.max, other.max) - Math.max(line.min, other.min) - stem) * 3;
          } else if (crossing(line, other, 5)) {
            score += 24;
          }
        }
      }
      if (score >= scoreBest) return;
      const middleSegments = segments(simplify(candidate.slice(1, -1)));
      if (middleSegments.some(line => !safe(line.a, line.b))) return;
      // Avoid doubling back along the arrow's own approach segment.
      if (route.length < 2 || !close(distance(route[0], candidate[1]) + distance(candidate[1], route[1]), distance(route[0], route[1]))
          || !close(distance(route.at(-1), candidate.at(-2)) + distance(candidate.at(-2), route.at(-2)), distance(route.at(-1), route.at(-2)))) return;
      scoreBest = score;
      best = route;
    }

    for (const out of exitSides) {
      if (from.decision && out !== preferredExit && best) break;
      for (const into of entrySides) {
        let start = portOf(from, out, !from.decision && fromSide === out ? fromOffset : 0);
        let end = portOf(to, into, !to.decision && toSide === into ? toOffset : 0);
        const [dx, dy] = normals[out];
        const [ix, iy] = normals[into];
        if (dx === -ix && dy === -iy) {
          // Mermaid's polygon stroke can offset an otherwise aligned diamond by half a unit.
          const offset = dx ? end.y - start.y : end.x - start.x;
          if (Math.abs(offset) <= 1) {
            if (!from.decision && !fromSide) start = portOf(from, out, offset);
            else if (!to.decision && !toSide) end = portOf(to, into, -offset);
          }
        }
        const a = shift(start, normals[out], Math.max(stem, edge.startGap + 8));
        const b = shift(end, normals[into], Math.max(stem, edge.endGap + 8));
        if (!safe(start, a, edge.from) || !safe(end, b, edge.to)) continue;
        // Entering and leaving a node at the same port can look like a false junction.
        const opposed = routed.filter(other => (other.edge.to === edge.from && distance(start, other.end) < 2)
          || (other.edge.from === edge.to && distance(end, other.start) < 2)).length;
        const penalty = (out === preferredExit ? 0 : portPenalty) + (into === preferredEntry ? 0 : portPenalty) + opposed * 240;
        if (penalty >= scoreBest) continue;
        const add = (waypoints, extra = 0) => consider([start, ...waypoints, end], penalty + extra);
        if (close(a.x, b.x) || close(a.y, b.y)) add([a, b]);
        add([a, {x: a.x, y: b.y}, b]);
        add([a, {x: b.x, y: a.y}, b]);
        if (guide.length) {
          add(orthogonalPoints([a, ...guide, b], horizontal));
          add(orthogonalPoints([a, ...guide, b], !horizontal));
        }
        if (Number.isFinite(manualLane)) add([a, {x: manualLane, y: a.y}, {x: manualLane, y: b.y}, b], -80);
        for (const x of new Set([middle(a.x, b.x), ...xLanes])) add([a, {x, y: a.y}, {x, y: b.y}, b]);
        for (const y of new Set([middle(a.y, b.y), ...yLanes])) add([a, {x: a.x, y}, {x: b.x, y}, b]);
      }
    }
    return best;
  }

  const routed = [];
  for (const edge of edges) {
    const route = chooseRoute(edge);
    if (!route) {
      if ([edge.from, edge.to].some(node => autoPositions.has(node) || compacted.has(node))) {
        for (const [node, transform] of autoPositions) node.setAttribute('transform', transform);
        for (const {shape, points} of compacted.values()) shape.setAttribute('points', points);
        straightenFlowchartEdges(svg, direction, source, false);
        return;
      }
      if (!restoreLayout) continue;
      restoreLayout();
      straightenFlowchartEdges(svg, direction, source.replace(spec[0], ''));
      return;
    }
    const trimmed = [...route];
    trimmed[0] = endInset(route[0], route[1], edge.startGap);
    trimmed[trimmed.length - 1] = endInset(route.at(-1), route.at(-2), edge.endGap);
    const lines = segments(trimmed);
    const item = {edge, lines, points: trimmed, start: route[0], end: route.at(-1),
      approach: segments(route).at(-1), jumps: new Map(), gaps: [], squareCorners: new Set()};
    routed.push(item);
    used.push(...lines.slice(0, -1), {...item.approach, approach: true, edge});
  }

  function cornerRadius(before, corner, after) {
    return Math.min(9, distance(before, corner) * .45, distance(corner, after) * .45);
  }

  const junctions = [];
  const trunks = [...routed].sort((a, b) => distance(b.approach.a, b.end) - distance(a.approach.a, a.end));
  for (const [i, branch] of trunks.entries()) {
    if (branch.points.length < 3) continue;
    const trunk = trunks.slice(0, i).find(other => !other.joined && canShareArrow(branch.edge, other.edge)
      && sameApproach(branch.approach, other.approach));
    if (!trunk || distance(branch.approach.a, branch.end) < 8) continue;
    const junction = {...branch.approach.a, [trunk.approach.fixed]: trunk.approach.at};
    const before = trunk.lines.at(-2);
    if (before && distance(trunk.approach.a, junction) <= cornerRadius(before.a, before.b, trunk.end) + epsilon) {
      trunk.squareCorners.add(trunk.lines.length - 2);
    }
    branch.points.splice(-2, 2, junction);
    branch.lines = segments(branch.points);
    branch.joined = true;
    junctions.push(junction);
  }
  used.splice(0, used.length, ...routed.flatMap(item => item.lines));

  function jumpClearance(point, line, list, i) {
    const coordinate = line.axis;
    const before = i ? cornerRadius(list[i - 1].a, line.a, line.b) : 2;
    const after = i + 1 < list.length ? cornerRadius(line.a, line.b, list[i + 1].b) : 2;
    return Math.min(Math.abs(point[coordinate] - line.a[coordinate]) - before,
      Math.abs(point[coordinate] - line.b[coordinate]) - after);
  }

  // A transparent gap beneath the arc keeps line jumps visible on any fill and in exported SVG.
  for (const [i, a] of routed.entries()) {
    for (const b of routed.slice(i + 1)) {
      for (const [j, first] of a.lines.entries()) {
        for (const [k, second] of b.lines.entries()) {
          const point = crossing(first, second, 0);
          if (!point || junctions.some(junction => distance(junction, point) < 8)) continue;
          const radius = Math.min(5, jumpClearance(point, first, a.lines, j) - 2,
            jumpClearance(point, second, b.lines, k) - 2);
          if (radius < 2.5) continue;
          const [over, line, under] = first.axis === 'x' ? [a, first, b] : [b, second, a];
          const jumps = over.jumps.get(line) || [];
          if (jumps.some(jump => Math.abs(jump.x - point.x) < jump.radius + radius + 2)) continue;
          const jump = {...point, radius};
          jumps.push(jump);
          over.jumps.set(line, jumps);
          under.gaps.push(jump);
        }
      }
    }
  }

  function draw({edge, points, lines, jumps, gaps, joined, squareCorners}, index) {
    const pair = point => {
      const {x, y} = transformPoint(point, edge.toPath);
      return x + ',' + y;
    };
    let d = 'M' + pair(points[0]);
    for (const [i, line] of lines.entries()) {
      const next = points[i + 2];
      const corner = line.b;
      const order = Math.sign(line.b.x - line.a.x);
      for (const {x, y, radius} of (jumps.get(line) || []).sort((a, b) => order * (a.x - b.x))) {
        const start = {x: x - order * radius, y};
        const end = {x: x + order * radius, y};
        d += 'L' + pair(start) + 'Q' + pair({x, y: y - 2 * radius}) + ' ' + pair(end);
      }
      if (next && !squareCorners.has(i)) {
        const radius = cornerRadius(line.a, corner, next);
        d += 'L' + pair(endInset(corner, line.a, radius)) + 'Q' + pair(corner) + ' ' + pair(endInset(corner, next, radius));
      } else {
        d += 'L' + pair(corner);
      }
    }
    edge.path.setAttribute('d', d);
    if (joined) edge.path.removeAttribute('marker-end');
    if (!gaps.length) return;
    const id = svg.id + '-line-jump-' + index;
    const {x, y, width, height} = edge.path.getBBox();
    const bounds = {x: x - 12, y: y - 12, width: width + 24, height: height + 24};
    const mask = svgElement('mask', {id, maskUnits: 'userSpaceOnUse', ...bounds});
    mask.append(svgElement('rect', {...bounds, fill: 'white'}));
    for (const point of gaps) {
      const local = transformPoint(point, edge.toPath);
      mask.append(svgElement('rect', {x: local.x - 3, y: local.y - point.radius - 2, width: 6, height: point.radius + 5, fill: 'black'}));
    }
    let defs = svg.querySelector('defs');
    if (!defs) {
      defs = svgElement('defs');
      svg.prepend(defs);
    }
    defs.append(mask);
    edge.path.setAttribute('mask', 'url(#' + id + ')');
  }

  const routedLabels = new Set(routed.map(({edge}) => edge.label));
  const labelBoxes = Array.from(labels.values()).filter(label => label.hasAttribute('transform') && !routedLabels.has(label)).map(boxOf);
  function placeLabel({edge, lines}) {
    const label = edge.label;
    if (!label?.transform.baseVal.numberOfItems) return;
    const original = boxOf(label);
    const w = (original.b.x - original.a.x) / 2;
    const h = (original.b.y - original.a.y) / 2;
    const pos = label.transform.baseVal.getItem(0).matrix;
    const rootToParent = label.parentNode.getCTM().inverse().multiply(root.getCTM());
    let best;
    let bestCost = Infinity;
    for (const line of lines) {
      const half = line.axis === 'x' ? w : h;
      const min = line.min + half + 4;
      const max = line.max - half - 4;
      if (max < min) continue;
      const near = Math.min(max, Math.max(min, original.center[line.axis]));
      for (const along of [near, middle(min, max), min, max]) {
        const offset = (line.axis === 'x' ? h : w) + 5;
        for (const sign of [-1, 1]) {
          const center = {[line.axis]: along, [line.fixed]: line.at + sign * offset};
          const box = {a: {x: center.x - w, y: center.y - h}, b: {x: center.x + w, y: center.y + h}};
          const cost = distance(center, original.center);
          if (cost >= bestCost || [...obstacles, ...labelBoxes].some(({a, b}) =>
            a.x < box.b.x + 3 && b.x > box.a.x - 3 && a.y < box.b.y + 3 && b.y > box.a.y - 3)
            || used.some(line => segmentTouches(line.a, line.b, box, 2))) continue;
          best = {center, box};
          bestCost = cost;
        }
      }
    }
    if (!best) {
      labelBoxes.push(original);
      return;
    }
    const old = transformPoint(original.center, rootToParent);
    const next = transformPoint(best.center, rootToParent);
    label.setAttribute('transform', 'translate(' + (pos.e + next.x - old.x) + ', ' + (pos.f + next.y - old.y) + ')');
    labelBoxes.push(best.box);
  }

  routed.forEach(draw);
  routed.forEach(placeLabel);
  const {x, y, width, height} = root.getBBox();
  svg.setAttribute('viewBox', [x - 8, y - 8, width + 16, height + 16].join(' '));
}
