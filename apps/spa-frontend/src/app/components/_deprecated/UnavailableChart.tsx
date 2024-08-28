import classNames from 'classnames';

export enum UnavailabilityType {
  NO_DATA = 'NO_DATA',
  STILL_PROCESSING = 'STILL_PROCESSING',
  COMING_SOON = 'COMING_SOON',
}

interface UnavailableChartProps {
  unavailability: UnavailabilityType;
  error?: boolean;
}

const unavailabilityMessage: Record<UnavailabilityType, string> = {
  [UnavailabilityType.NO_DATA]: 'Complete the questionnaires to see this chart',
  [UnavailabilityType.STILL_PROCESSING]: 'Still processing...',
  [UnavailabilityType.COMING_SOON]: 'Coming soon...',
};

function UnavailableChart(props: UnavailableChartProps) {
  return (
    <div className="absolute inset-0">
      <div
        className={classNames(
          'absolute top-1/2 left-1/2 -translate-y-1/2 -translate-x-1/2 shadow-xl rounded-xl z-10 text-xl w-2/3 mx-auto py-3 text-center',
          props.error ? 'bg-red-500' : 'bg-gray-50',
        )}
      >
        {props.error ? (
          <p>Error while fetching data</p>
        ) : (
          unavailabilityMessage[props.unavailability]
        )}
      </div>
    </div>
  );
}

export { UnavailableChart };
