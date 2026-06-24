// One itinerary, rendered as a route strip (the signature element): airport
// codes joined by flight legs, with an amber layover bead at each stop. A
// compact segment list underneath carries the full times / flight numbers.

import { Fragment } from "react";
import { formatDuration, formatClock, dayOffset } from "../format.js";

export default function Itinerary({ itinerary }) {
  const { segments, layovers, stops, totalDurationMinutes, totalPrice } = itinerary;
  const firstDep = segments[0].departureTime;

  // Build the strip's nodes: origin, each stop (with its layover), destination.
  const nodes = [{ code: segments[0].origin, time: formatClock(firstDep) }];
  segments.forEach((seg, i) => {
    if (i < segments.length - 1) {
      nodes.push({ code: seg.destination, layover: layovers[i].durationMinutes });
    } else {
      nodes.push({
        code: seg.destination,
        time: formatClock(seg.arrivalTime),
        day: dayOffset(firstDep, seg.arrivalTime),
      });
    }
  });

  const stopsLabel = stops === 0 ? "Direct" : stops === 1 ? "1 stop" : "2 stops";

  return (
    <article className="itin">
      <div className="itin-top">
        <span className="duration">{formatDuration(totalDurationMinutes)}</span>
        <span className={`stops-pill${stops === 0 ? " direct" : ""}`}>{stopsLabel}</span>
        <span className="price">${totalPrice.toFixed(0)}</span>
      </div>

      <div className="strip">
        {nodes.map((node, i) => (
          <Fragment key={i}>
            <div className="node">
              <span className="code">{node.code}</span>
              {node.time && (
                <span className="time">
                  {node.time}
                  {node.day > 0 && <sup className="day">+{node.day}</sup>}
                </span>
              )}
              {node.layover != null && (
                <span className="layover-tag">{formatDuration(node.layover)}</span>
              )}
            </div>
            {i < segments.length && (
              <div className="leg">
                <div className="meta">
                  <span className="fno">{segments[i].flightNumber}</span> ·{" "}
                  {formatDuration(segments[i].durationMinutes)}
                </div>
                <div className="wire" />
              </div>
            )}
          </Fragment>
        ))}
      </div>

      <div className="segments">
        {segments.map((seg, i) => {
          const segDay = dayOffset(seg.departureTime, seg.arrivalTime);
          return (
            <Fragment key={i}>
              <div className="seg">
                <span className="clock">
                  {formatClock(seg.departureTime)}–{formatClock(seg.arrivalTime)}
                  {segDay > 0 && <sup className="day"> +{segDay}</sup>}
                </span>
                <span className="path">
                  <b>{seg.origin}</b> → <b>{seg.destination}</b>{" "}
                  <span style={{ color: "var(--ink-faint)" }}>{seg.airline}</span>
                </span>
                <span className="tail">
                  <span className="fno">{seg.flightNumber}</span> ·{" "}
                  {formatDuration(seg.durationMinutes)} · ${seg.price.toFixed(0)}
                </span>
              </div>
              {i < layovers.length && (
                <div className="layover-line">
                  ↳ {formatDuration(layovers[i].durationMinutes)} layover in{" "}
                  {layovers[i].airport}
                </div>
              )}
            </Fragment>
          );
        })}
      </div>
    </article>
  );
}
