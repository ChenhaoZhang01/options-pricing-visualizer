import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

/**
 * Renders a single Greek (or price) as a function of spot price using D3.
 * A reference line marks the strike and the current spot.
 */
export default function GreekChart({ data, greek, strike, spot }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!data || data.length === 0) return;
    const width = 680;
    const height = 420;
    const margin = { top: 20, right: 24, bottom: 44, left: 64 };

    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const x = d3
      .scaleLinear()
      .domain(d3.extent(data, (d) => d.S))
      .range([margin.left, width - margin.right]);

    const y = d3
      .scaleLinear()
      .domain(d3.extent(data, (d) => d[greek]))
      .nice()
      .range([height - margin.bottom, margin.top]);

    // Axes
    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(8))
      .attr("color", "#8b949e");
    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(6))
      .attr("color", "#8b949e");

    // Axis labels
    svg
      .append("text")
      .attr("x", width / 2)
      .attr("y", height - 6)
      .attr("fill", "#8b949e")
      .attr("text-anchor", "middle")
      .text("Spot price (S)");
    svg
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", 16)
      .attr("fill", "#8b949e")
      .attr("text-anchor", "middle")
      .text(greek);

    // Zero line
    if (y.domain()[0] < 0 && y.domain()[1] > 0) {
      svg
        .append("line")
        .attr("x1", margin.left)
        .attr("x2", width - margin.right)
        .attr("y1", y(0))
        .attr("y2", y(0))
        .attr("stroke", "#30363d");
    }

    // Strike reference line
    svg
      .append("line")
      .attr("x1", x(strike))
      .attr("x2", x(strike))
      .attr("y1", margin.top)
      .attr("y2", height - margin.bottom)
      .attr("stroke", "#f0883e")
      .attr("stroke-dasharray", "4 4");

    // The curve
    const line = d3
      .line()
      .x((d) => x(d.S))
      .y((d) => y(d[greek]))
      .curve(d3.curveMonotoneX);

    svg
      .append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#1f6feb")
      .attr("stroke-width", 2.5)
      .attr("d", line);

    // Current spot marker
    const here = data.reduce((a, b) =>
      Math.abs(b.S - spot) < Math.abs(a.S - spot) ? b : a
    );
    svg
      .append("circle")
      .attr("cx", x(here.S))
      .attr("cy", y(here[greek]))
      .attr("r", 5)
      .attr("fill", "#3fb950");
  }, [data, greek, strike, spot]);

  return <svg ref={ref} width="100%" />;
}
