import { Navigate, createBrowserRouter } from 'react-router-dom';
import { RouterProvider } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthenticationPage } from './pages/AuthenticationPage';
import { BreadcrumbProvider } from './providers/BreadcrumbContext';
import { DashboardPage } from './pages/DashboardPage';
import { PersonalityContent } from './components/PersonalityContent';
import { TraitCardDetails } from './components/TraitCardDetails';
import { IntjCardDetails } from './components/IntjCardDetails';
import { SixteenPFCardDetails } from './components/SixteenPFCardDetails';
import { PoliticsContent } from './components/PoliticsContent';
import { CompassDetails } from './components/CompassDetails';
import { MFTDetails } from './components/MFTDetails';
import { LandingPage } from './pages/LandingPage';

import { CareerContent } from './components/CareerContent';
import { RadarChartDetails } from './components/RadarChartDetails';
import { PersonalityContainer } from './components/containers/PersonalityContainer';

import { SocialLayout } from './components/SocialLayout';
import { SocialPage } from './pages/SocialPage';
import { ProfilePage } from './pages/ProfilePage';
import { FileUploadPage } from './pages/FileUploadPage';
import { QuestionnairePage } from './pages/QuestionnairePage';
import { AuthProvider } from './providers/AuthProvider';
import { AccountSettings } from './pages/AccountSettingsPage';
import { AccountSettingsLayout } from './components/AccountSettingsLayout';
import { LifeJourneys } from './components/LifeJourneys';
import { LifeJourneyLayout } from './components/LifeJourneyLayout';
import { StreamChatPage } from './pages/StreamChatPage';
import { StreamChatProvider } from './providers/StreamChatProvider';

const reactRouter = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/login',
    element: <AuthenticationPage authenticationType="login" />,
  },
  {
    path: '/signup',
    element: <AuthenticationPage authenticationType="signup" />,
  },
  {
    path: '/fileUpload',
    element: <FileUploadPage />,
  },
  {
    path: '/questionnaire',
    element: <QuestionnairePage />,
  },
  // {
  //   path: '/fakeOauth',
  //   element: <FakeOauthPage />,
  // },
  {
    path: '/dashboard',
    element: <DashboardPage />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard/personality" replace />,
      },
      {
        path: 'personality',
        element: (
          <PersonalityContainer>
            <PersonalityContent />
          </PersonalityContainer>
        ),
      },
      { path: 'personality/trait/:title', element: <TraitCardDetails /> },
      { path: 'personality/mbti/:title', element: <IntjCardDetails /> },
      { path: 'personality/trait2/:title', element: <SixteenPFCardDetails /> },
      { path: 'politics', element: <PoliticsContent /> },
      { path: 'politics/compass', element: <CompassDetails /> },
      { path: 'politics/mft', element: <MFTDetails /> },
      { path: 'career', element: <CareerContent /> },
      { path: 'career/radar', element: <RadarChartDetails /> },
    ],
  },
  {
    path: '/life-journeys',
    element: <LifeJourneyLayout />,
    children: [
      {
        index: true,
        element: <LifeJourneys />,
      },
    ],
  },
  {
    path: '/socials',
    element: <SocialLayout />,
    children: [
      {
        index: true,
        element: <SocialPage />,
      },
      {
        path: ':profile',
        element: <ProfilePage />,
        children: [
          {
            path: '/socials/:profile/personality',
            element: <PersonalityContent />,
          },
          { path: '/socials/:profile/politics', element: <PoliticsContent /> },
          { path: '/socials/:profile/career', element: <CareerContent /> },
        ],
      },
    ],
  },
  {
    path: '/chat',
    element: <StreamChatPage />,
  },
  {
    path: '/account-settings',
    element: <AccountSettingsLayout />,
    children: [
      {
        index: true,
        element: <AccountSettings />,
      },
    ],
  },
]);

export function App() {
  return (
    <AuthProvider>
      <StreamChatProvider>
        <BreadcrumbProvider>
          <RouterProvider router={reactRouter} />
          <Toaster position="bottom-right" reverseOrder={false} />
        </BreadcrumbProvider>
      </StreamChatProvider>
    </AuthProvider>
  );
}
