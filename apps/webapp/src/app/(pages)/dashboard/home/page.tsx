import { HomePieChart } from '../../../components/home-pie-chart';
import { getCategoryCounts } from '../../../actions/getCategoryCounts';
import { AiChat } from '../../../components/ai-chat';

export default async function Home() {
  const data = await getCategoryCounts();
  return (
    <div className="flex flex-row gap-4">
      <HomePieChart data={data} />
      <AiChat />
    </div>
  );
}
