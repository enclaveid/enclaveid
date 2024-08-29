import { useState } from 'react';
import { Virtuoso } from 'react-virtuoso';
import { NonLatentCard } from '../NonLatentCard';
import { SocialCard } from '../SocialCard';

export function InfiniteCardLoader({
  query,
  cardComponent: Card,
}: {
  query: any;
  cardComponent: typeof NonLatentCard | typeof SocialCard;
}) {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const loadMore = async (startIndex, stopIndex) => {
    if (isLoading || !hasMore) return;

    setIsLoading(true);
    try {
      const newItems = await query({
        start: startIndex,
        limit: stopIndex - startIndex + 1,
      });
      setItems((prevItems) => [...prevItems, ...newItems]);
      setHasMore(newItems.length > 0);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const ItemRenderer = ({ item, index }) => {
    if (item) {
      return <Card interest={item} />;
    } else {
      // return <Card loading={true} />;
    }
  };

  return (
    <Virtuoso
      style={{ height: '100%', width: '100%' }}
      totalCount={hasMore ? items.length + 1 : items.length}
      overscan={200}
      endReached={() => loadMore(items.length, items.length + 20)}
      itemContent={(index) => (
        <ItemRenderer item={items[index]} index={index} />
      )}
    />
  );
}
