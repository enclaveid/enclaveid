'use client';

import { usePathname } from 'next/navigation';
import {
  BreadcrumbItem,
  BreadcrumbList,
  Breadcrumb,
} from '@enclaveid/ui/breadcrumb';

export function DashboardBreadcrumb() {
  const pathname = usePathname();

  const paths = pathname.split('/').filter(Boolean);
  const breadcrumbs = paths.map((path, index) => {
    const href = '/' + paths.slice(0, index + 1).join('/');
    const label = path
      .split('-')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
    return { href, label };
  });

  // return (
  //   <Breadcrumb>
  //     <BreadcrumbList>
  //       {breadcrumbs.map((crumb, index) => (
  //         <BreadcrumbItem key={crumb.href}>
  //           {index === breadcrumbs.length - 1 ? (
  //             <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
  //           ) : (
  //             <BreadcrumbLink href={crumb.href}>{crumb.label}</BreadcrumbLink>
  //           )}
  //           {index < breadcrumbs.length - 1 && <BreadcrumbSeparator />}
  //         </BreadcrumbItem>
  //       ))}
  //     </BreadcrumbList>
  //   </Breadcrumb>
  // );

  // TODO: we only display the last breadcrumb for now
  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          {breadcrumbs[breadcrumbs.length - 1].label}
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
}
