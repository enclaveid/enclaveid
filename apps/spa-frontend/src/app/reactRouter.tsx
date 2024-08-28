import { AuthenticationPage } from './pages/AuthenticationPage';
import { Navigate, Outlet, createBrowserRouter } from 'react-router-dom';
import { DashboardPage } from './pages/DashboardPage';
import { PersonalityContent } from './components/PersonalityContent';
import { TraitCardDetails } from './components/TraitCardDetails';
import { MbtiCardDetails } from './components/MbtiCardDetails';
import { SixteenPFCardDetails } from './components/SixteenPFCardDetails';
import { PoliticsContent } from './components/PoliticsContent';
import { CompassDetails } from './components/CompassDetails';
import { MFTDetails } from './components/MFTDetails';
import { LandingPage } from './pages/LandingPage';

import { CareerContent } from './components/CareerContent';
import { RadarChartDetails } from './components/RadarChartDetails';
import { PersonalityContainer } from './components/containers/PersonalityContainer';

import { SocialPage } from './pages/SocialPage';
import { ProfilePage } from './pages/ProfilePage';
import { FileUploadPage } from './pages/onboarding/FileUploadPage';
import { QuestionnairePage } from './pages/onboarding/QuestionnairePage';
import { AccountSettings } from './pages/AccountSettingsPage';
import { StreamChatPage } from './pages/StreamChatPage';
import { CommonLayout } from './components/CommonLayout';
import { OwnInterests } from './components/OwnInterests';
import { IntroPage } from './pages/onboarding/IntroPage';
import { PurposeSelectionPage } from './pages/onboarding/PurposeSelectionPage';
import { RequireAuth } from './providers/AuthProvider';
import { OnboardingGuard } from './components/guards/OnboardingGuard';
import { EmailConfirmationGuard } from './components/guards/EmailConfirmationGuard';
import { EmailConfirmationPage } from './pages/onboarding/EmailConfirmationPage';
import { StreamChatProvider } from './providers/StreamChatProvider';
import { OnboardingSkipsProvider } from './providers/OnboardingSkipsProvider';

export const reactRouter = createBrowserRouter([
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
    path: '/confirm-email',
    element: (
      <RequireAuth>
        <EmailConfirmationPage />
      </RequireAuth>
    ),
  },
  {
    path: '/onboarding',
    element: (
      <RequireAuth>
        <EmailConfirmationGuard>
          <OnboardingSkipsProvider>
            <OnboardingGuard />
          </OnboardingSkipsProvider>
        </EmailConfirmationGuard>
      </RequireAuth>
    ),
    children: [
      {
        index: true,
        element: <IntroPage />,
      },
      {
        path: 'purposeSelection',
        element: <PurposeSelectionPage />,
      },
      {
        path: 'fileUpload',
        element: <FileUploadPage />,
      },
      {
        path: 'questionnaire',
        element: <QuestionnairePage />,
      },
      // {
      //   path: '/fakeOauth',
      //   element: <FakeOauthPage />,
      // },
    ],
  },
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
      { path: 'personality/mbti/:title', element: <MbtiCardDetails /> },
      { path: 'personality/trait2/:title', element: <SixteenPFCardDetails /> },
      { path: 'politics', element: <PoliticsContent /> },
      { path: 'politics/compass', element: <CompassDetails /> },
      { path: 'politics/mft', element: <MFTDetails /> },
      { path: 'career', element: <CareerContent /> },
      { path: 'career/radar', element: <RadarChartDetails /> },
    ],
  },
  {
    path: '/interests',
    element: (
      <CommonLayout>
        <Outlet />
      </CommonLayout>
    ),
    children: [
      {
        index: true,
        element: <OwnInterests />,
      },
    ],
  },
  {
    path: '/socials',
    element: (
      <CommonLayout>
        <Outlet />
      </CommonLayout>
    ),
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
    element: (
      <StreamChatProvider>
        <StreamChatPage />
      </StreamChatProvider>
    ),
  },
  {
    path: '/account-settings',
    element: (
      <CommonLayout>
        <Outlet />
      </CommonLayout>
    ),
    children: [
      {
        index: true,
        element: <AccountSettings />,
      },
    ],
  },
]);
