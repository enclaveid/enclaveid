import { backgroundPattern } from '../utils/backgroundPattern';

interface LoadingPageProps {
  customMessage?: string;
}

export function LoadingPage(props: LoadingPageProps) {
  return (
    <div
      className="flex items-center justify-center h-screen"
      style={backgroundPattern}
    >
      <div className="flex items-center space-x-4">
        <svg
          className="w-8 h-8 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M12 2a10 10 0 000 20m0-18v4m0 14v4m-8-8h4m10 0h4"
          ></path>
        </svg>
        <span className="text-gray-600">
          {props.customMessage ?? 'Connecting to server...'}
        </span>
      </div>
    </div>
  );
}
