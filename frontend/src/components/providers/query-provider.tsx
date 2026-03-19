"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  // useState ensures each browser session gets its own QueryClient instance,
  // preventing state from being shared between requests on the server.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Data is considered fresh for 30s by default; individual hooks override this.
            staleTime: 30_000,
            // Retry failed requests once before surfacing an error.
            retry: 1,
            // Don't refetch when the window regains focus — hooks set explicit intervals.
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
