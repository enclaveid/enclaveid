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
  is_emotional: boolean;
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
  strong_emotional_implications?: string;
}

// Add this function before the useEffect
const createTooltip = (
  svg: d3.Selection<SVGGElement, unknown, null, undefined>,
  mouseX: number,
  mouseY: number,
  width: number,
  mainText: string,
  dateText?: string,
) => {
  // Remove any existing tooltips
  svg.selectAll('.tooltip-group').remove();

  const tooltipGroup = svg.append('g').attr('class', 'tooltip-group');

  // Create temporary text element to measure text width
  const tempText = tooltipGroup
    .append('text')
    .style('visibility', 'hidden')
    .text(mainText);

  // Calculate text metrics
  const textWidth = Math.min(300, tempText.node().getComputedTextLength());
  tempText.remove();

  // Add background rectangle
  const tooltipBg = tooltipGroup
    .append('rect')
    .attr('class', 'tooltip-bg')
    .attr('fill', 'white')
    .attr('stroke', '#ccc')
    .attr('rx', 4)
    .attr('ry', 4)
    .attr('opacity', 1); // Fix opacity

  // Add date text if provided
  let textYOffset = 0;
  if (dateText) {
    tooltipGroup
      .append('text')
      .attr('class', 'tooltip-date')
      .attr('x', 8) // Add padding
      .attr('y', 20)
      .text(dateText);
    textYOffset = 40;
  }

  // Add main text with wrapping
  const tooltipText = tooltipGroup
    .append('text')
    .attr('class', 'tooltip-text')
    .attr('x', 8)
    .attr('y', textYOffset);

  // Split text into segments based on bold markers
  const segments = mainText.split('**');
  let yPos = 0;
  const x = 8;
  const lineHeight = 1.2; // ems
  const maxWidth = 1000;

  segments.forEach((segment, i) => {
    const isBold = i % 2 === 1; // Alternate between normal and bold

    // Split segment into words
    const words = segment.split(/\s+/);
    let line: string[] = [];

    words.forEach((word) => {
      if (word === '') return;

      line.push(word);
      const testTspan = tooltipText
        .append('tspan')
        .attr('font-weight', isBold ? 'bold' : 'normal')
        .text(line.join(' '));

      if (testTspan.node().getComputedTextLength() > maxWidth - 16) {
        line.pop();
        if (line.length) {
          tooltipText
            .append('tspan')
            .attr('x', x)
            .attr('dy', yPos === 0 ? '1em' : `${lineHeight}em`)
            .attr('font-weight', isBold ? 'bold' : 'normal')
            .text(line.join(' '));
          yPos++;
        }
        line = [word];
      }
      testTspan.remove();
    });

    if (line.length) {
      tooltipText
        .append('tspan')
        .attr('x', x)
        .attr('dy', yPos === 0 ? '1em' : `${lineHeight}em`)
        .attr('font-weight', isBold ? 'bold' : 'normal')
        .text(line.join(' '));
      yPos++;
    }
  });

  // Calculate tooltip dimensions
  const tooltipBBox = tooltipGroup.node().getBBox();
  const padding = 8;

  // Position background
  tooltipBg
    .attr('x', tooltipBBox.x - padding)
    .attr('y', tooltipBBox.y - padding)
    .attr('width', tooltipBBox.width + padding * 2)
    .attr('height', tooltipBBox.height + padding * 2);

  // Position entire tooltip group
  const tooltipX = Math.min(
    width - tooltipBBox.width - padding * 2,
    Math.max(0, mouseX - tooltipBBox.width / 2),
  );
  const tooltipY = mouseY - tooltipBBox.height - 20;

  tooltipGroup.attr('transform', `translate(${tooltipX},${tooltipY})`);

  return tooltipGroup;
};

export function Storyline({ data }: { data: StorylineData[] }) {
  const svgRef = useRef(null);
  const fixedAxisRef = useRef(null);
  const originalOrderRef = useRef<number[]>([]);

  useEffect(() => {
    if (!data || !data.length) return;

    // Clear previous charts
    d3.select(svgRef.current).selectAll('*').remove();
    d3.select(fixedAxisRef.current).selectAll('*').remove();

    // Convert BigInts to regular numbers for d3 grouping
    const processedData = data.map((d) => ({
      ...d,
      coarse_cluster_label: Number(d.coarse_cluster_label),
      fine_cluster_label: Number(d.fine_cluster_label),
      fine_cluster_transitions: d.fine_cluster_transitions.map((t) => ({
        cluster_id: Number(t.cluster_id),
        probability: t.probability,
      })),
    }));

    // Process data to group by fine and coarse clusters
    const groupedData = d3.group(processedData, (d) => d.coarse_cluster_label);

    // Calculate time extent across all data
    const timeExtent = d3.extent(processedData, (d) => new Date(d.start_date));

    // Set up dimensions
    const margin = { top: 40, right: 40, bottom: 40, left: 500 };
    const extraTopPadding = 300;
    const width = 1200 - margin.left - margin.right;
    const barHeight = 25;
    const barPadding = 2;
    const coarseClusterPadding = 100;

    // Calculate total height based on actual content
    let totalHeight = margin.top + margin.bottom + extraTopPadding;
    groupedData.forEach((coarseGroup) => {
      const fineGroups = d3.group(coarseGroup, (d) => d.fine_cluster_label);
      const coarseClusterHeight = fineGroups.size * (barHeight + barPadding);
      totalHeight += coarseClusterHeight + coarseClusterPadding;
    });

    // Update height with the calculated total
    const height = totalHeight;

    // Create scales
    const timeScale = d3.scaleTime().domain(timeExtent).range([0, width]);

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height)
      .append('g')
      .attr(
        'transform',
        `translate(${margin.left},${margin.top + extraTopPadding})`,
      );

    // Create fixed axis SVG
    const fixedAxisSvg = d3
      .select(fixedAxisRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', margin.top)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Add white background for the fixed axis
    fixedAxisSvg
      .append('rect')
      .attr('x', -margin.left)
      .attr('y', -margin.top)
      .attr('width', width + margin.left + margin.right)
      .attr('height', margin.top)
      .attr('fill', 'white');

    // Add the fixed timeline axis
    const xAxisTop = d3.axisTop(timeScale);
    fixedAxisSvg.call(xAxisTop);

    // Add vertical timeline separator to fixed axis
    fixedAxisSvg
      .append('line')
      .attr('x1', 0)
      .attr('x2', 0)
      .attr('y1', -margin.top)
      .attr('y2', 0)
      .attr('stroke', '#666')
      .attr('stroke-width', 2);

    // Add vertical timeline separator FIRST (before any other elements)
    svg
      .append('line')
      .attr('x1', 0)
      .attr('x2', 0)
      .attr('y1', -margin.top) // Extend line to top of chart
      .attr('y2', height - margin.bottom)
      .attr('stroke', '#666')
      .attr('stroke-width', 2);

    // Create axis
    const xAxis = d3.axisBottom(timeScale);
    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(xAxis);

    // Store original order of coarse clusters
    originalOrderRef.current = Array.from(groupedData.keys());

    // Calculate emotional counts for each coarse cluster
    const emotionalCounts = new Map<number, number>();
    groupedData.forEach((coarseGroup, coarseLabel) => {
      const emotionalCount = coarseGroup.filter((d) => d.is_emotional).length;
      emotionalCounts.set(coarseLabel, emotionalCount);
    });

    // Sort coarse clusters by emotional count (descending)
    originalOrderRef.current = Array.from(groupedData.keys()).sort((a, b) => {
      const countA = emotionalCounts.get(a) || 0;
      const countB = emotionalCounts.get(b) || 0;
      return countB - countA;
    });

    const renderVisualization = (
      orderedCoarseClusters: number[],
      highlightedClusters?: Set<number>,
      transitionProbabilities?: Map<number, number>,
      selectedFineCluster?: number,
    ) => {
      // Clear previous chart content but keep the timeline separator
      svg.selectAll('*').remove();

      // Redraw timeline separator
      svg
        .append('line')
        .attr('x1', 0)
        .attr('x2', 0)
        .attr('y1', -margin.top)
        .attr('y2', height - margin.bottom)
        .attr('stroke', '#666')
        .attr('stroke-width', 2);

      let yOffset = 0;
      orderedCoarseClusters.forEach((coarseLabel) => {
        const coarseGroup = groupedData.get(coarseLabel);
        if (!coarseGroup) return;

        // Calculate height needed for this coarse cluster
        const fineGroups = d3.group(coarseGroup, (d) => d.fine_cluster_label);
        const coarseClusterHeight = fineGroups.size * (barHeight + barPadding);

        // Add background for the entire coarse cluster group
        svg
          .append('rect')
          .attr('x', -margin.left)
          .attr('y', yOffset - coarseClusterPadding / 2)
          .attr('width', width + margin.left)
          .attr('height', coarseClusterHeight + coarseClusterPadding)
          .attr('fill', () => {
            if (transitionProbabilities?.has(coarseLabel)) {
              // Use red with opacity based on probability
              const probability = transitionProbabilities.get(coarseLabel) || 0;
              return d3.interpolate('#fff5f5', '#feb2b2')(probability);
            }
            return highlightedClusters?.has(coarseLabel)
              ? '#f0f7ff'
              : '#f8f8f8';
          })
          .attr('opacity', 0.5);

        // Add probability percentage text if applicable
        if (transitionProbabilities?.has(coarseLabel)) {
          const probability = transitionProbabilities.get(coarseLabel) || 0;
          svg
            .append('text')
            .attr('x', -margin.left + 10) // Position at the start of the cluster
            .attr('y', yOffset + 20) // Position near the top of the cluster
            .attr('fill', '#e53e3e') // Red text
            .attr('font-weight', 'bold')
            .text(`${Math.ceil(probability * 100 * 100) / 100}%`);
        }

        // Add border lines for the group
        svg
          .append('line')
          .attr('x1', -margin.left)
          .attr('x2', width)
          .attr('y1', yOffset - coarseClusterPadding / 2)
          .attr('y2', yOffset - coarseClusterPadding / 2)
          .attr('stroke', '#ccc')
          .attr('stroke-width', 1);

        // Initialize fineClusterIndex for this coarse cluster
        let fineClusterIndex = 0;

        // Group by fine cluster within each coarse cluster
        fineGroups.forEach((records, fineLabel) => {
          // Calculate start and end dates for the group
          const start = d3.min(records, (d) => new Date(d.start_date));
          const end = d3.max(records, (d) => new Date(d.start_date));

          // Calculate y position for this fine cluster
          const fineClusterY =
            yOffset + fineClusterIndex * (barHeight + barPadding);

          // Modify the bar color with a higher red baseline
          const color = (() => {
            if (Number(fineLabel) === selectedFineCluster) {
              return '#e53e3e'; // Darker red for selected cluster
            } else if (transitionProbabilities?.has(Number(fineLabel))) {
              const probability =
                transitionProbabilities.get(Number(fineLabel)) || 0;
              // Start from a higher baseline red (#fecaca) to darker red (#ef4444)
              return d3.interpolate('#fecaca', '#ef4444')(probability);
            } else {
              return d3.interpolateBlues(
                0.3 + ((Number(fineLabel) % 10) * 0.6) / 10,
              );
            }
          })();

          // Draw bar with updated color
          svg
            .append('rect')
            .attr('x', timeScale(start))
            .attr('y', fineClusterY)
            .attr('width', timeScale(end) - timeScale(start))
            .attr('height', barHeight)
            .attr('fill', color)
            .attr('rx', 5)
            .attr('ry', 5)
            .attr('class', 'gantt-bar')
            .on('mouseover', function (event) {
              d3.select(this).attr('opacity', 0.8);
              const [mouseX, mouseY] = d3.pointer(event, svg.node());
              // Get the first record to show cluster information
              const clusterRecord = records[0];
              createTooltip(
                svg,
                mouseX,
                mouseY,
                width,
                `Fine Cluster ${fineLabel}: ${clusterRecord.fine_cluster_summary}`,
                `${records.length} conversations`,
              );
            })
            .on('mouseout', function () {
              d3.select(this).attr('opacity', 1);
              svg.selectAll('.tooltip-group').remove();
            });

          // Add probability percentage if applicable
          if (transitionProbabilities?.has(Number(fineLabel))) {
            const probability =
              transitionProbabilities.get(Number(fineLabel)) || 0;
            svg
              .append('text')
              .attr('x', timeScale(start) - 45) // Position just before the bar
              .attr('y', fineClusterY + barHeight / 2 + 4) // Vertically center with the bar
              .attr('fill', '#e53e3e') // Red text
              .attr('font-weight', 'bold')
              .attr('font-size', '12px')
              .text(`${Math.ceil(probability * 100 * 100) / 100}%`);
          }

          fineClusterIndex++;

          // Add dots for individual data points
          const datePositions = new Map<number, number>(); // Track dots per x-position
          records.forEach((record) => {
            const xPos = timeScale(new Date(record.start_date));
            const baseY = fineClusterY + barHeight / 2;

            const dotsAtPosition = datePositions.get(xPos) || 0;
            const verticalOffset =
              dotsAtPosition * 8 - Math.min(dotsAtPosition, 3) * 4;
            datePositions.set(xPos, dotsAtPosition + 1);

            const dotGroup = svg
              .append('g')
              .attr('class', 'activity-point')
              .attr(
                'transform',
                `translate(${xPos},${baseY + verticalOffset})`,
              );

            // Base circle (green if core, yellow if not)
            dotGroup
              .append('circle')
              .attr('r', 4)
              .attr('fill', record.fine_cluster_is_core ? 'green' : 'yellow')
              .attr('stroke', 'black')
              .attr('stroke-width', 1);

            // Add red half-circle if emotional
            if (record.is_emotional) {
              dotGroup
                .append('path')
                .attr('d', 'M -4,0 A 4,4 0 0,1 4,0 L 0,0 Z')
                .attr('fill', 'red')
                .attr('stroke', 'black')
                .attr('stroke-width', 1);
            }

            dotGroup
              .on('mouseover', function (event) {
                dotGroup.attr(
                  'transform',
                  `translate(${xPos},${baseY + verticalOffset}) scale(1.5)`,
                );
                const [mouseX, mouseY] = d3.pointer(event, svg.node());
                const dateStr = new Date(
                  record.start_date,
                ).toLocaleDateString();
                const tooltipText = record.is_emotional
                  ? `${dateStr} **${record.title}** ${record.summary.replace(/\*\*/g, '')}

**Emotional Implications** ${record.strong_emotional_implications}`
                  : `${dateStr} **${record.title}** ${record.summary.replace(/\*\*/g, '')}`;
                createTooltip(svg, mouseX, mouseY, width, tooltipText);
              })
              .on('mouseout', function () {
                dotGroup.attr(
                  'transform',
                  `translate(${xPos},${baseY + verticalOffset}) scale(1)`,
                );
                svg.selectAll('.tooltip-group').remove();
              })
              .on('click', function (event) {
                event.stopPropagation();

                // Remove any existing time indicator lines and labels
                svg
                  .selectAll('.time-indicator, .time-indicator-label')
                  .remove();
                fixedAxisSvg
                  .selectAll('.time-indicator, .time-indicator-label')
                  .remove();

                // Get the x position of the dot and format the date
                const xPos = timeScale(new Date(record.start_date));
                const dateStr = new Date(
                  record.start_date,
                ).toLocaleDateString();

                // Add the line to main SVG with 5px top margin
                svg
                  .append('line')
                  .attr('class', 'time-indicator')
                  .attr('x1', xPos)
                  .attr('x2', xPos)
                  .attr('y1', -margin.top + 25) // Added 25px margin from top
                  .attr('y2', height - margin.bottom)
                  .attr('stroke', 'red')
                  .attr('stroke-width', 1);

                // Add date label to main SVG
                svg
                  .append('text')
                  .attr('class', 'time-indicator-label')
                  .attr('x', xPos + 5)
                  .attr('y', 0) // Position at the top of the visible area
                  .attr('fill', 'red')
                  .attr('font-size', '12px')
                  .text(dateStr);

                // Add the line to fixed axis SVG with 5px top margin
                fixedAxisSvg
                  .append('line')
                  .attr('class', 'time-indicator')
                  .attr('x1', xPos)
                  .attr('x2', xPos)
                  .attr('y1', -margin.top + 25) // Added 25px margin from top
                  .attr('y2', 0)
                  .attr('stroke', 'red')
                  .attr('stroke-width', 1);

                // Add date label to fixed axis SVG
                fixedAxisSvg
                  .append('text')
                  .attr('class', 'time-indicator-label')
                  .attr('x', xPos + 5)
                  .attr('y', -margin.top / 2) // Position in the middle of the fixed axis area
                  .attr('fill', 'red')
                  .attr('font-size', '12px')
                  .text(dateStr);

                // Existing transition handling code
                const transitions = record.fine_cluster_transitions;
                const transitionProbabilities = new Map<number, number>();

                // Set current fine cluster probability to 1
                transitionProbabilities.set(
                  Number(record.fine_cluster_label),
                  1,
                );

                // Add probabilities from transitions
                transitions.forEach((transition) => {
                  transitionProbabilities.set(
                    transition.cluster_id,
                    transition.probability,
                  );
                });

                // Get coarse clusters for ordering
                const targetCoarseClusters = new Set<number>();
                targetCoarseClusters.add(coarseLabel);

                // Add coarse clusters of transition targets
                transitions.forEach((transition) => {
                  const transitionCoarseCluster = processedData.find(
                    (d) =>
                      Number(d.fine_cluster_label) === transition.cluster_id,
                  )?.coarse_cluster_label;
                  if (transitionCoarseCluster !== undefined) {
                    targetCoarseClusters.add(Number(transitionCoarseCluster));
                  }
                });

                // Inside the dot click handler, replace the order creation logic with:
                const currentIndex = orderedCoarseClusters.indexOf(coarseLabel);

                // Split target clusters into those that should go before and after
                const targetClustersArray = Array.from(
                  targetCoarseClusters,
                ).filter((c) => c !== coarseLabel);
                const midPoint = targetClustersArray.length / 2;
                const targetsBefore = targetClustersArray.slice(
                  0,
                  Math.floor(midPoint),
                );
                const targetsAfter = targetClustersArray.slice(
                  Math.floor(midPoint),
                );

                const newOrder = [
                  // Keep non-target clusters that were before the current one
                  ...orderedCoarseClusters
                    .slice(0, currentIndex)
                    .filter((c) => !targetCoarseClusters.has(c)),
                  // Add half of target clusters before
                  ...targetsBefore,
                  // Keep the selected cluster in its position
                  coarseLabel,
                  // Add remaining target clusters after
                  ...targetsAfter,
                  // Add remaining non-target clusters that were after
                  ...orderedCoarseClusters
                    .slice(currentIndex + 1)
                    .filter((c) => !targetCoarseClusters.has(c)),
                ];

                // Render with new order and fine cluster probabilities
                renderVisualization(
                  newOrder,
                  targetCoarseClusters,
                  transitionProbabilities,
                  Number(record.fine_cluster_label),
                );
              });
          });
        });

        // Update coarse cluster label position to center vertically
        const wrapText = (text: string, width: number): string[] => {
          return text.match(new RegExp(`.{1,${width}}(\\s|$)`, 'g')) || [text];
        };

        const lines = wrapText(coarseGroup[0].cluster_title, 80);
        const lineHeight = 16;
        const totalTextHeight = lines.length * lineHeight;
        const startY = yOffset + (coarseClusterHeight - totalTextHeight) / 2;

        lines.forEach((line, i) => {
          // For the first line, prepend the coarse cluster number in bold
          if (i === 0) {
            svg
              .append('text')
              .attr('x', -490)
              .attr('y', startY + lineHeight) // Use startY + lineHeight for baseline alignment
              .attr('class', 'coarse-label')
              .style('font-size', '12px')
              .style('font-weight', 'bold')
              .text(`${coarseLabel}. `);

            // Adjust x position for the title text to account for the cluster number
            svg
              .append('text')
              .attr('x', -470)
              .attr('y', startY + lineHeight)
              .attr('class', 'coarse-label')
              .style('font-size', '12px')
              .text(line.trim());
          } else {
            svg
              .append('text')
              .attr('x', -490)
              .attr('y', startY + (i + 1) * lineHeight)
              .attr('class', 'coarse-label')
              .style('font-size', '12px')
              .text(line.trim());
          }
        });

        // Update yOffset to account for all fine clusters plus padding
        yOffset += coarseClusterHeight + coarseClusterPadding;
      });
    };

    // Initial render with original order and no highlights
    renderVisualization(originalOrderRef.current);

    // Update background click handler to remove highlights
    svg.on('click', () => {
      renderVisualization(originalOrderRef.current);
    });
  }, [data]);

  return (
    <div className="relative w-full">
      {/* Fixed axis SVG */}
      <svg
        ref={fixedAxisRef}
        className="w-full sticky top-0 z-10"
        style={{
          minWidth: '1200px',
          backgroundColor: 'white',
        }}
      />
      {/* Update the container to allow proper scrolling */}
      <div className="w-full overflow-x-auto overflow-y-visible">
        <svg
          ref={svgRef}
          className="w-full"
          style={{
            minWidth: '1200px',
          }}
        />
      </div>
    </div>
  );
}
