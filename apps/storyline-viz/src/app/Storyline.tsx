import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface ClusterTransition {
  cluster_id: bigint;
  probability: number;
}

interface DateTimeQuestion {
  date: string;
  time: string;
  question: string;
}

interface StorylineData {
  start_date: string;
  start_time: string;
  title: string;
  emotional: boolean;
  coarse_cluster_label: bigint;
  fine_cluster_label: bigint;
  fine_cluster_is_core: boolean;
  fine_cluster_transitions: ClusterTransition[];
  conversation_id: string;
  datetime_conversations: string;
  datetime_questions: DateTimeQuestion[];
  summary: string;
  summary_embedding: number[]; // Float32Array of shape 4096
  fine_cluster_summary: string;
  cluster_title: string;
}

/**
 *
 * @param data - OrderedDict([('start_date', String), ('start_time', String), ('title', String), ('emotional', Boolean), ('coarse_cluster_label', Int64), ('fine_cluster_label', Int64), ('fine_cluster_is_core', Boolean), ('fine_cluster_transitions', List(Struct({'cluster_id': Int64, 'probability': Float64}))), ('conversation_id', String), ('datetime_conversations', String), ('datetime_questions', List(Struct({'date': String, 'time': String, 'question': String}))), ('summary', String), ('summary_embedding', Array(Float32, shape=(4096,))), ('fine_cluster_summary', String), ('cluster_title', String)])
 * @returns
 */
export function Storyline({ data }: { data: StorylineData[] }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!data || !data.length) return;

    // Clear previous chart
    d3.select(svgRef.current).selectAll('*').remove();

    // Convert BigInts to regular numbers for d3 grouping
    const processedData = data.map((d) => ({
      ...d,
      coarse_cluster_label: Number(d.coarse_cluster_label),
      fine_cluster_label: Number(d.fine_cluster_label),
    }));

    // Process data to group by fine and coarse clusters
    const groupedData = d3.group(processedData, (d) => d.coarse_cluster_label);

    // Calculate time extent across all data
    const timeExtent = d3.extent(processedData, (d) => new Date(d.start_date));

    // Set up dimensions
    const margin = { top: 40, right: 40, bottom: 40, left: 100 };
    const width = 1200 - margin.left - margin.right;
    const barHeight = 25;
    const barPadding = 2;
    const coarseClusterPadding = 20;

    // Calculate total height based on number of coarse clusters
    const height =
      groupedData.size * (barHeight + coarseClusterPadding) +
      margin.top +
      margin.bottom;

    // Create scales
    const timeScale = d3.scaleTime().domain(timeExtent).range([0, width]);

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create axis
    const xAxis = d3.axisBottom(timeScale);
    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(xAxis);

    // Process and draw bars
    let yOffset = 0;
    groupedData.forEach((coarseGroup, coarseLabel) => {
      // Group by fine cluster within each coarse cluster
      const fineGroups = d3.group(coarseGroup, (d) => d.fine_cluster_label);

      // Calculate height needed for this coarse cluster
      const coarseClusterHeight = fineGroups.size * (barHeight + barPadding);

      // Draw fine cluster bars
      let fineClusterIndex = 0;
      fineGroups.forEach((records, fineLabel) => {
        // Calculate start and end dates for the group
        const start = d3.min(records, (d) => new Date(d.start_date));
        const end = d3.max(records, (d) => new Date(d.start_date));

        // Calculate y position for this fine cluster
        const fineClusterY =
          yOffset + fineClusterIndex * (barHeight + barPadding);

        // Generate unique color based on fine cluster label
        const color = d3.interpolateBlues(
          0.3 + ((Number(fineLabel) % 10) * 0.6) / 10,
        );

        // Draw bar
        svg
          .append('rect')
          .attr('x', timeScale(start))
          .attr('y', fineClusterY) // Use calculated y position
          .attr('width', timeScale(end) - timeScale(start))
          .attr('height', barHeight)
          .attr('fill', color)
          .attr('rx', 5)
          .attr('ry', 5)
          .attr('class', 'gantt-bar')
          .on('mouseover', function (event) {
            d3.select(this).attr('opacity', 0.8);

            // Get mouse position relative to the SVG container
            const [mouseX, mouseY] = d3.pointer(event, svg.node());

            const tooltipGroup = svg.append('g').attr('class', 'tooltip-group');

            // Prepare text content
            const tooltipText = `Fine Label ${fineLabel} (${records.length} records): ${records[0].fine_cluster_summary}`;
            const dateText = `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`;

            // Create temporary text element to measure text width
            const tempText = tooltipGroup
              .append('text')
              .style('visibility', 'hidden')
              .text(tooltipText);

            // Calculate text metrics
            const textWidth = Math.min(
              300,
              tempText.node().getComputedTextLength(),
            );
            tempText.remove();

            // Improved text wrapping function
            function wrapText(selection, width) {
              selection.each(function () {
                const text = d3.select(this);
                const words = text.text().split(/\s+/).reverse();
                const lineHeight = 1.1; // ems
                const y = text.attr('y');
                const dy = parseFloat(text.attr('dy'));

                let line = [];
                let lineNumber = 0;
                let word = words.pop();
                let tspan = text
                  .text(null)
                  .append('tspan')
                  .attr('x', 0)
                  .attr('y', y)
                  .attr('dy', dy + 'em');

                while (word) {
                  line.push(word);
                  tspan.text(line.join(' '));
                  if (tspan.node().getComputedTextLength() > width) {
                    line.pop();
                    tspan.text(line.join(' '));
                    line = [word];
                    tspan = text
                      .append('tspan')
                      .attr('x', 0)
                      .attr('y', y)
                      .attr('dy', ++lineNumber * lineHeight + dy + 'em')
                      .text(word);
                  }
                  word = words.pop();
                }
              });
            }

            // Add background rectangle (will adjust size after text is added)
            const tooltipBg = tooltipGroup
              .append('rect')
              .attr('class', 'tooltip-bg')
              .attr('fill', 'white')
              .attr('stroke', '#ccc')
              .attr('rx', 4)
              .attr('ry', 4);

            // Add date text
            const dateLabel = tooltipGroup
              .append('text')
              .attr('class', 'tooltip-date')
              .attr('x', 0)
              .attr('y', 0)
              .attr('dy', '1em')
              .text(dateText);

            // Add main text with wrapping
            const mainText = tooltipGroup
              .append('text')
              .attr('class', 'tooltip-text')
              .attr('x', 0)
              .attr('y', 20)
              .attr('dy', '1em')
              .text(tooltipText)
              .call(wrapText, textWidth);

            // Calculate tooltip dimensions after text is added
            const tooltipBBox = tooltipGroup.node().getBBox();

            // Position tooltip and background
            const padding = 10;
            tooltipBg
              .attr('x', tooltipBBox.x - padding)
              .attr('y', tooltipBBox.y - padding)
              .attr('width', tooltipBBox.width + padding * 2)
              .attr('height', tooltipBBox.height + padding * 2);

            // Position entire tooltip group
            const tooltipX = Math.min(
              width - tooltipBBox.width - padding,
              Math.max(0, mouseX - tooltipBBox.width / 2),
            );
            const tooltipY = Math.max(0, mouseY - tooltipBBox.height - 20);

            tooltipGroup.attr(
              'transform',
              `translate(${tooltipX},${tooltipY})`,
            );
          })
          .on('mousemove', function (event) {
            const [mouseX, mouseY] = d3.pointer(event, svg.node());
            const tooltipGroup = svg.select('.tooltip-group');
            const tooltipBBox = tooltipGroup.node().getBBox();

            const tooltipX = Math.min(
              width - tooltipBBox.width - 10,
              Math.max(0, mouseX - tooltipBBox.width / 2),
            );
            const tooltipY = Math.max(0, mouseY - tooltipBBox.height - 20);

            tooltipGroup.attr(
              'transform',
              `translate(${tooltipX},${tooltipY})`,
            );
          })
          .on('mouseout', function (event) {
            d3.select(this).attr('opacity', 1);
            svg.selectAll('.tooltip-group').remove();
          });

        fineClusterIndex++;
      });

      // Update coarse cluster label position to center vertically
      svg
        .append('text')
        .attr('x', -90)
        .attr('y', yOffset + coarseClusterHeight / 2)
        .attr('class', 'coarse-label')
        .style('font-weight', 'bold')
        .text(`Coarse ${coarseLabel}`);

      // Update yOffset to account for all fine clusters plus padding
      yOffset += coarseClusterHeight + coarseClusterPadding;
    });
  }, [data]);

  return (
    <div className="w-full overflow-x-auto">
      <svg ref={svgRef} className="w-full" style={{ minWidth: '1200px' }} />
    </div>
  );
}
