import { Transition } from '@headlessui/react';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';
import { UseTRPCQueryResult } from '@trpc/react-query/dist/shared';
import { useEffect, useState } from 'react';

export function LoadingCheckmark({
  booleanQuery,
}: {
  booleanQuery: UseTRPCQueryResult<boolean, any>;
}) {
  const isLoading = booleanQuery.isLoading;

  const [status, setStatus] = useState<'loading' | 'success' | 'failure'>(
    'loading',
  );

  useEffect(() => {
    if (booleanQuery.isSuccess) {
      if (booleanQuery.data) {
        setStatus('success');
      } else {
        setStatus('failure');
      }
    }
  }, [booleanQuery]);

  return (
    <div className="relative flex items-center justify-center h-12 w-12 rounded-lg">
      <Transition
        show={true}
        enter="transition-opacity duration-300"
        enterFrom="opacity-0"
        enterTo="opacity-100"
        leave="transition-opacity duration-300"
        leaveFrom="opacity-100"
        leaveTo="opacity-0"
      >
        <div
          className={`absolute inset-0 flex items-center justify-center transition-opacity duration-300 ${isLoading ? 'opacity-100' : 'opacity-0'}`}
        >
          <svg
            className="animate-spin h-8 w-8 text-gray-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
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
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        </div>
      </Transition>

      <Transition
        show={true}
        enter="transition-opacity duration-300"
        enterFrom="opacity-0"
        enterTo="opacity-100"
        leave="transition-opacity duration-300"
        leaveFrom="opacity-100"
        leaveTo="opacity-0"
      >
        <div
          className={`absolute inset-0 flex items-center justify-center transition-opacity duration-300 ${status === 'success' ? 'opacity-100' : 'opacity-0'}`}
        >
          <CheckCircleIcon className="h-8 w-8 text-green-500" />
        </div>
      </Transition>

      <Transition
        show={true}
        enter="transition-opacity duration-300"
        enterFrom="opacity-0"
        enterTo="opacity-100"
        leave="transition-opacity duration-300"
        leaveFrom="opacity-100"
        leaveTo="opacity-0"
      >
        <div
          className={`absolute inset-0 flex items-center justify-center transition-opacity duration-300 ${status === 'failure' ? 'opacity-100' : 'opacity-0'}`}
        >
          <XCircleIcon className="h-8 w-8 text-red-500" />
        </div>
      </Transition>
    </div>
  );
}
