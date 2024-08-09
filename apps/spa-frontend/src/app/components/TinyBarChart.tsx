import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  LogarithmicScale,
} from 'chart.js';

ChartJS.register(
  BarElement,
  CategoryScale,
  LogarithmicScale,
  LinearScale,
  Tooltip,
  Legend,
);

interface TinyBarChartProps {
  dates: string[];
  maxBars?: number;
}

export function TinyBarChart({ dates, maxBars = 30 }: TinyBarChartProps) {
  // Parse dates into Date objects
  const parsedDates = dates.map((date) => new Date(date));

  // Find the min and max dates
  const minDate = new Date(Math.min(...parsedDates));
  const maxDate = new Date(Math.max(...parsedDates));

  // Calculate the interval size (in days) for each bar
  const totalDays =
    (maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24);
  const intervalSize = Math.ceil(totalDays / maxBars);

  // Initialize intervals
  const intervals: { start: Date; end: Date; count: number }[] = [];

  for (let i = 0; i < maxBars; i++) {
    const start = new Date(minDate.getTime());
    start.setDate(minDate.getDate() + i * intervalSize);

    const end = new Date(minDate.getTime());
    end.setDate(minDate.getDate() + (i + 1) * intervalSize);

    intervals.push({ start, end, count: 0 });
  }

  // Aggregate the data into intervals
  parsedDates.forEach((date) => {
    for (const interval of intervals) {
      if (date >= interval.start && date < interval.end) {
        interval.count++;
        break;
      }
    }
  });

  // Prepare labels and counts for the chart
  const labels = intervals.map((interval) => {
    const startLabel = interval.start.toLocaleDateString();
    const endLabel = interval.end.toLocaleDateString();
    return `${startLabel} - ${endLabel}`;
  });

  const counts = intervals.map((interval) => interval.count);

  const data = {
    labels,
    datasets: [
      {
        label: 'Activity Count',
        data: counts,
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    maintainAspectRatio: false,
    scales: {
      x: {
        display: true,
        ticks: {
          callback: function (value: string, index: number) {
            // Show only the first and last labels
            if (index === Math.floor(labels.length / 2)) {
              return `${dates[0]} - ${dates[dates.length - 1]}`;
            }
          },
          maxRotation: 0,
          minRotation: 0,
        },
      },
      y: {
        type: 'logarithmic', // Set the y-axis to use a logarithmic scale
        display: false,
        beginAtZero: true, // Optional: set to true if you want the scale to start at 1
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        caretSize: 0,
        enabled: true,
        callbacks: {
          title: (tooltipItems) => {
            // Display the interval as the tooltip title
            const index = tooltipItems[0].dataIndex;
            return labels[index];
          },
          label: (tooltipItem) => `Count: ${tooltipItem.raw}`,
        },
      },
    },
    elements: {
      bar: {
        borderRadius: 2,
      },
    },
  };

  return (
    <div style={{ width: '150px', height: '50px' }}>
      <Bar data={data} options={options} />
    </div>
  );
}
