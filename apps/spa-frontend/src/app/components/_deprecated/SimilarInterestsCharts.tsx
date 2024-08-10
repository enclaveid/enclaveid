import { Bar } from 'react-chartjs-2';
import {
  Chart,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js';

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const HOVER_LINE_MAX_LENGTH = 200;

const options = {
  indexAxis: 'y',
  responsive: true,
  plugins: {
    tooltip: {
      callbacks: {
        label: (context) => {
          const hoverLabel = context.dataset.hoverLabel[context.dataIndex];
          const value = context.raw;
          return [
            value,
            Array.from(
              { length: Math.ceil(hoverLabel.length / HOVER_LINE_MAX_LENGTH) },
              (v, i) =>
                hoverLabel.slice(
                  i * HOVER_LINE_MAX_LENGTH,
                  i * HOVER_LINE_MAX_LENGTH + HOVER_LINE_MAX_LENGTH,
                ),
            ),
          ].flat();
        },
      },
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      ticks: {
        max: 1,
      },
    },
  },
};

function prepareData(data: SimilarInterest[]) {
  const top20 = data.slice(0, 20);

  return {
    labels: top20.map((item) => ''), // Empty labels
    datasets: [
      {
        label: 'Cosine Similarity',
        data: top20.map((item) => item.cosineSimilarity),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
        hoverBackgroundColor: 'rgba(75, 192, 192, 1)',
        hoverBorderColor: 'rgba(75, 192, 192, 1)',
        // TODO: Just removing the first 15 characters for now which always contain the same text
        hoverLabel: top20.map((item) => item.summary.slice(15)),
      },
    ],
  };
}

interface SimilarInterest {
  summary: string;
  cosineSimilarity: number;
}

interface SimilarInterestsChartsProps {
  proactiveInterests: SimilarInterest[];
  reactiveInterests: SimilarInterest[];
}

export function SimilarInterestsCharts({
  proactiveInterests,
  reactiveInterests,
}: SimilarInterestsChartsProps) {
  return (
    <div>
      <h3>Proactive interests</h3>
      <Bar data={prepareData(proactiveInterests)} options={options} />

      <h3>Reactive interests</h3>
      <Bar data={prepareData(reactiveInterests)} options={options} />
    </div>
  );
}
